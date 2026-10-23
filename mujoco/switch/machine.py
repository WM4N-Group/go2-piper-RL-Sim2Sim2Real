"""执行/路由层：顺序任务 + 每技能入口契约 + 通用连续命令接管。"""
import numpy as np
from runtime import infer, blend_command


class Machine:
    def __init__(self, runtime, tasks, blend_seconds=.20):
        self.r, self.tasks = runtime, tasks
        self.blend_seconds = blend_seconds
        self.index = -1
        self.phase = 'startup'
        self.events, self.results = [], []
        self.started = runtime.sim.data.time
        self.age = 0.
        self.complete = False
        self.finish = None
        self.command = runtime.last
        self.switch_metrics = []
        self.guard = runtime.push['finish'].CollisionGuard(runtime.sim, runtime.push['finish'].FinishConfig())

    def event(self, name, **values):
        item = dict(time=float(self.r.sim.data.time), event=name, **values)
        self.events.append(item)
        print(item, flush=True)

    def enter(self):
        r,p = self.r,self.r.sim
        self.index += 1
        if self.index == len(self.tasks):
            self.complete = True
            self.phase = 'complete'
            self.event('sequence_complete')
            return
        self.previous_kind = getattr(self,'kind',None)
        self.item = self.tasks[self.index]
        self.kind = self.item['skill']
        self.prepare_started = None
        if self.kind=='push':
            from push_entry import PushEntry
            self.push_entry=PushEntry(r,r.last)
            self.preparation=self.push_entry
            self.phase='prepare'
            self.prepare_started=float(p.data.time)
            self.event('prepare_entry',skill='push')
            return
        if self.kind=='climb' and self.previous_kind=='push' and getattr(r,'near_climb',False):
            from climb_entry import ClimbEntry
            self.preparation=ClimbEntry(r,self.item)
            self.item['approach']=self.preparation.goal.tolist()
            self.item['startup_ramp_seconds']=self.preparation.config.policy_ramp_seconds
            self.item['approach_speed']=self.preparation.config.policy_speed
            self.phase='prepare'
            self.prepare_started=float(p.data.time)
            self.event('prepare_entry',skill='climb',goal=self.preparation.goal.tolist())
            return
        self.activate()

    def activate(self):
        r,p = self.r,self.r.sim
        # 只读交接状态；任何入口检查失败都报错，不把机器人搬到标准起点。
        before = np.r_[p.data.qpos,p.data.qvel].copy()
        queue_before = [a.copy() for a in p.queue]
        speed = float(np.linalg.norm(p.data.qvel[:3]))
        if speed>.12 or r.n.state()[3]>.30 or np.max(abs(p.data.qpos[p.qids[12:]]))>.12:
            raise RuntimeError('entry_not_stationary_or_arm_not_safe')
        if self.kind == 'nav':
            if self.previous_kind!='nav':
                r.reset_nav_history(self.item.get('surface_height',0.))
            self.nav = r.make_nav(self.item)
        else:
            goal = np.array(self.item.get('approach',[-.08,r.box_y if self.kind=='push' else 0.]))
            yaw_error = abs(r.nav['navigation'].wrap_angle(r.n.state()[2]))
            if np.linalg.norm(p.data.qpos[:2]-goal)>.16 or yaw_error>.25:
                raise RuntimeError('entry_approach_pose_outside_contract')
            if self.kind == 'push':
                r.push_enter()
                self.finish = None
            else:
                r.climb_enter(self.item)
        assert np.array_equal(before,np.r_[p.data.qpos,p.data.qvel]), 'Skill entry changed physical state'
        assert len(queue_before)==len(p.queue) and all(np.array_equal(a,b) for a,b in zip(queue_before,p.queue))
        self.started = float(p.data.time)
        self.old_command = r.last
        self.phase = 'blend'
        self.event('enter', index=self.index, skill=self.kind, speed=speed,
                   xy=p.data.qpos[:2].tolist(), yaw=r.n.state()[2], state_jump=0., delay_queue_preserved=True)
        self.switch_metrics.append(dict(index=self.index,skill=self.kind,max_target_step_rad=0.,
            max_requested_torque_step_nm=0.,blend_seconds=self.blend_seconds))

    def update(self):
        r,p = self.r,self.r.sim
        self.age = float(p.data.time)-self.started
        if self.phase == 'startup':
            if self.age>=6.:
                feet = [p.model.body(f'{leg}_foot').id for leg in ('FR','FL','RR','RL')]
                if np.linalg.norm(p.data.qvel[:3])<.04 and np.all(p.forces[feet,2]>3.):
                    self.enter()
                elif self.age>10.:
                    raise RuntimeError('startup_not_settled')
            return
        if self.complete:
            if self.kind=='nav':
                r.n.set_wbc_command(np.zeros(3),r.n.ee_command)
                r.n.set_action(infer(r.nav_actor,r.n.observation(),r.device))
            return
        if self.phase=='prepare':
            age = float(p.data.time)-self.prepare_started
            self.preparation.update()
            if self.preparation.ready:
                self.event('entry_prepared',skill=self.kind,seconds=age,
                           metrics=self.preparation.metrics)
                self.activate()
            return
        if self.kind == 'nav':
            state = r.nav_state(self.started)
            velocity = self.nav.update(state)
            r.n.set_wbc_command(velocity,r.n.ee_command)
            r.n.set_action(infer(r.nav_actor,r.n.observation(),r.device))
            if self.nav.arrived:
                self.results.append(dict(skill='nav',seconds=self.age,position_error=self.nav.distance,
                    yaw_error=self.nav.yaw_error,successful=True))
                self.event('skill_complete',skill='nav',error_m=self.nav.distance)
                self.enter()
                return
            if self.age>60.:
                raise RuntimeError('nav_timeout:'+str(self.nav.stability_checks(state)))
        elif self.kind == 'push' and self.finish is None:
            obs = p.observation()
            outputs = [infer(actor,obs,r.device) for actor in r.push_actors]
            with r.push.active():
                p.set_action(*outputs)
                p.episode_length_buf += 1
                flags = p.termination()
            bad = [k for k,v in flags.items() if v and k!='box_settled']
            if bad:
                self.event('push_safety_failure',flags=bad,
                    hand=p.robot.data.body_pos_w[0,p.controller.hand_id].tolist(),
                    contact=p.scene.sensors['box_contact_hand'].data.contact_pos_w.tolist(),
                    force=p.scene.sensors['box_contact_hand'].data.force_matrix_w.tolist(),
                    yaw=r.n.state()[2],tilt=r.n.state()[3],
                    path=int(p.controller.safe_approach_index[0]),face=bool(p.controller.approach_face_ready[0]))
                raise RuntimeError('push:'+','.join(bad))
            push_ready=flags['box_settled']
            if hasattr(r,'staircase'):
                push_ready=r.staircase.push_ready(p,push_ready)
            if push_ready:
                self.finish = r.push['finish'].FinishController(p)
                self.event('push_exit_retract',**(r.staircase.dock_metrics(p) if hasattr(r,'staircase') else {}))
            if self.age>48.:
                raise RuntimeError('push_timeout:'+str(r.staircase.dock_metrics(p)) if hasattr(r,'staircase') else 'push_timeout')
        elif self.kind == 'push':
            if self.finish.failure:
                raise RuntimeError(self.finish.failure)
            if self.finish.phase=='success':
                self.results.append(dict(skill='push',seconds=self.age,successful=True,
                    goal_error=float(np.linalg.norm(p.data.xpos[p.box_id,:2]-p.box_push_target[0,:2].numpy())),
                    finish=self.finish.report()))
                self.event('skill_complete',skill='push')
                self.enter()
                return
        elif self.kind == 'climb':
            c = r.c
            c.set_action(infer(r.climb_actor,c.observation(),r.device))
            state,reason = r.stop.status(*c.status())
            if state in ('failed','timeout'):
                raise RuntimeError('climb:'+reason)
            if state=='success':
                self.results.append(dict(skill='climb',seconds=self.age,successful=True,stop=r.stop.report()))
                self.event('skill_complete',skill='climb')
                self.enter()

    def next_command(self):
        r,p = self.r,self.r.sim
        if self.phase=='startup':
            return r.startup_command()
        if self.phase=='prepare':
            return self.preparation.command()
        if self.kind=='nav':
            new = r.nav_command()
        elif self.kind=='push':
            if self.finish is not None:
                new = self.finish.command()
            else:
                pm = r.push['model']
                new = r.Command(p.targets.copy(),np.zeros(18),pm.KP.copy(),pm.KD.copy(),np.zeros(18))
        else:
            new = r.climb_command(r.stop.command(r.c.policy_command()))
        age = p.data.time-self.started
        if age<self.blend_seconds and not self.complete:
            new = blend_command(r.Command,self.old_command,new,age/self.blend_seconds)
        elif self.phase=='blend':
            self.phase='run'
            self.event('blend_complete',skill=self.kind)
        if self.switch_metrics:
            m = self.switch_metrics[-1]
            if age<self.blend_seconds+.005:
                m['max_target_step_rad'] = max(m['max_target_step_rad'],float(np.max(abs(new.position-r.last.position))))
                q,qd = p.data.qpos[p.qids],p.data.qvel[p.dids]
                def torque(c):
                    return c.kp*(c.position-q)+c.kd*(c.velocity-qd)+c.feedforward
                m['max_requested_torque_step_nm'] = max(m['max_requested_torque_step_nm'],float(np.max(abs(torque(new)-torque(r.last)))))
        return new

    def after_step(self):
        if self.phase=='startup':
            return
        r = self.r
        if self.phase=='prepare':
            pass
        elif self.kind=='nav':
            self.nav.observe(r.nav_state(self.started))
        elif self.kind=='push' and self.finish is not None:
            self.finish.after_step()
            if self.finish.failure:
                raise RuntimeError(self.finish.failure)
        elif self.kind=='climb':
            r.stop.after_step()
            if r.stop.failure:
                raise RuntimeError(r.stop.failure)
        # 手端接触只在推箱阶段允许；收臂使用 Finish 自带的逐段和动态碰撞检查。
        reason = self.guard.check(r.sim.data.qpos[r.sim.qids[12:]],
            allow_hand_contact=self.kind=='push', joint_limits=False, record=True)
        if reason:
            raise RuntimeError('actual_collision_guard:'+reason)

"""Shared EXIT candidate on native Isaac; isolated from all training sources.

Hooks retain original failure checks, actuators, delay and arm compensation.
Native ascent becomes an entry event; it cannot terminate as full success.
Only one evaluated episode per environment is supported in this developer probe.
"""
import json
from pathlib import Path
import numpy as np
import torch
from exit_control import ExitController, EXIT_SPEC


def install(env, output):
    from isaaclab.utils.math import euler_xyz_from_quat
    output=Path(output);cfg=vars(env.task).copy()
    controllers=[ExitController(r.detach().cpu().numpy(),cfg) for r in env.reference]
    finished=np.zeros(env.num_envs,dtype=bool)
    traces=[[] for _ in controllers]
    view=env.robot.root_physx_view
    masses=view.get_masses().to(env.device)
    substep_count=np.zeros(env.num_envs,dtype=int)
    metadata=dict(body_names=env.robot.body_names,contact_body_names=env.contact.body_names,
        joint_ids=env.joint_ids,foot_ids=env.foot_ids,contact_feet=env.contact_feet,forbidden=env.forbidden,
        mass=masses.detach().cpu().tolist(),origins=env.scene.env_origins.detach().cpu().tolist(),
        reference=env.reference.detach().cpu().tolist(),physics_dt=env.physics_dt,control_dt=env.step_dt,
        exit_spec=EXIT_SPEC)
    (output/'exit_metadata.json').write_text(json.dumps(metadata))
    def cpu(t):return t.detach().cpu().numpy()
    # Observe the actual native delayed setpoints and PD inputs without an
    # additional buffer push or actuator evaluation.
    command_fields=('delayed_position','delayed_velocity','delayed_effort','pd_position','pd_velocity','computed_effort','applied_effort')
    command_witness={k:torch.zeros(env.num_envs,env.robot.num_joints,device=env.device) for k in command_fields}
    metadata['actuators']={}
    import inspect,hashlib
    for name,actuator in env.robot.actuators.items():
        ids=actuator.joint_indices
        source=Path(inspect.getsourcefile(type(actuator)))
        metadata['actuators'][name]=dict(joint_indices=[int(j) for j in ids],stiffness=cpu(actuator.stiffness).tolist(),
            damping=cpu(actuator.damping).tolist(),effort_limit=cpu(actuator.effort_limit).tolist(),
            delays=cpu(actuator.positions_delay_buffer.time_lags).tolist(),source=str(source),
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        for attr,key in (('positions_delay_buffer','delayed_position'),('velocities_delay_buffer','delayed_velocity'),('efforts_delay_buffer','delayed_effort')):
            buffer=getattr(actuator,attr);original_buffer_compute=buffer.compute
            def observe_buffer(value,_original=original_buffer_compute,_key=key,_ids=ids):
                delayed=_original(value)
                command_witness[_key][:,_ids]=delayed
                return delayed
            buffer.compute=observe_buffer
        original_compute=actuator.compute
        def observe_actuator(control_action,joint_pos,joint_vel,_original=original_compute,_actuator=actuator,_ids=ids):
            command_witness['pd_position'][:,_ids]=joint_pos
            command_witness['pd_velocity'][:,_ids]=joint_vel
            result=_original(control_action,joint_pos,joint_vel)
            command_witness['computed_effort'][:,_ids]=_actuator.computed_effort
            command_witness['applied_effort'][:,_ids]=_actuator.applied_effort
            return result
        actuator.compute=observe_actuator
    (output/'exit_metadata.json').write_text(json.dumps(metadata))
    original_reset=env._reset_idx;reset_events=[]
    def reset(ids):
        indices=ids.detach().cpu().tolist() if hasattr(ids,'detach') else list(ids)
        if any(not finished[i] for i in indices):raise RuntimeError('Reset before recorded terminal')
        reset_events.append(dict(env_ids=indices,after_terminal=True))
        (output/'reset_events.json').write_text(json.dumps(reset_events))
        return original_reset(ids)
    env._reset_idx=reset
    original_pre=env._pre_physics_step
    original_done=env._get_dones
    original_update=env.scene.update
    def pre(actions):
        original_pre(actions)
        for i,c in enumerate(controllers):
            if c.phase!='ACTIVE' and not finished[i]:
                env.targets[i]=torch.as_tensor(c.last_target,device=env.device,dtype=env.targets.dtype)
                env.actions[i]=(env.targets[i]-env.reference[i])/cfg['action_scale']
    env._pre_physics_step=pre
    def sample(dt,*args,**kwargs):
        result=original_update(dt,*args,**kwargs)
        d=env.robot.data
        com=(d.body_com_pos_w*masses[...,None]).sum(1)/masses.sum(1)[:,None]-env.scene.env_origins
        buffers={name:cpu(value) for name,value in dict(
            q=d.joint_pos[:,env.joint_ids],qd=d.joint_vel[:,env.joint_ids],root=d.root_state_w,
            body_pos=d.body_pos_w,root_velocity=d.root_link_lin_vel_w,angular=d.root_ang_vel_w,
            com=com,forces=env.contact.data.net_forces_w,target=env.targets,
            torque=d.applied_torque[:,env.joint_ids],height=env.heights,
            tilt=torch.acos((-d.projected_gravity_b[:,2]).clamp(-1,1)),
            arm_error=(d.joint_pos[:,env.joint_ids[12:]]-env.reference[:,12:]).abs().amax(-1)).items()}
        buffers.update({k:cpu(v[:,env.joint_ids]) for k,v in command_witness.items()})
        origins=metadata['origins']
        for i in range(env.num_envs):
            if finished[i]:continue
            substep_count[i]+=1
            physics_state=dict(feet=buffers['body_pos'][i,env.foot_ids]-origins[i],
                forces=buffers['forces'][i,env.contact_feet],com=buffers['com'][i],
                height=float(buffers['height'][i]),tilt=float(buffers['tilt'][i]),
                root_velocity=buffers['root_velocity'][i],angular_velocity=buffers['angular'][i],
                joint_velocity=buffers['qd'][i],arm_error=float(buffers['arm_error'][i]))
            controllers[i].observe_physics(physics_state,dt)
            record={k:buffers[k][i].copy() for k in ('q','qd','root','body_pos','root_velocity','com','forces','target','torque')}
            record.update({k:buffers[k][i].copy() for k in command_fields})
            record.update(time=substep_count[i]*env.physics_dt,phase=controllers[i].phase,hold=controllers[i].hold)
            traces[i].append(record)
        return result
    env.scene.update=sample
    def done():
        original_done()
        native=env.success.clone()
        d=env.robot.data
        roll,pitch,yaw=euler_xyz_from_quat(d.root_quat_w)
        roll=torch.atan2(roll.sin(),roll.cos());pitch=torch.atan2(pitch.sin(),pitch.cos())
        yaw=torch.atan2(yaw.sin(),yaw.cos())
        jac=view.get_jacobians()
        jac_ids=np.asarray(env.foot_ids)-(1 if env.robot.is_fixed_base else 0)
        assert jac.shape[1]==env.robot.num_bodies-(1 if env.robot.is_fixed_base else 0)
        gravity=view.get_gravity_compensation_forces()
        body_com=d.body_com_pos_w
        com=(body_com*masses[...,None]).sum(1)/masses.sum(1)[:,None]-env.scene.env_origins
        com_vel=(d.body_com_lin_vel_w*masses[...,None]).sum(1)/masses.sum(1)[:,None]
        kp=torch.zeros(env.num_envs,env.robot.num_joints,device=env.device);kd=kp.clone()
        for actuator in env.robot.actuators.values():
            kp[:,actuator.joint_indices]=actuator.stiffness
            kd[:,actuator.joint_indices]=actuator.damping
        buffers={name:cpu(value) for name,value in dict(
            feet=d.body_pos_w[:,env.foot_ids]-env.scene.env_origins[:,None,:],
            forces=env.contact.data.net_forces_w[:,env.contact_feet],com=com,com_velocity=com_vel,
            height=env.heights,tilt=torch.acos((-d.projected_gravity_b[:,2]).clamp(-1,1)),
            root_velocity=d.root_link_lin_vel_w,angular_velocity=d.root_ang_vel_w,
            joint_position=d.joint_pos[:,env.joint_ids],joint_velocity=d.joint_vel[:,env.joint_ids],
            arm_error=(d.joint_pos[:,env.joint_ids[12:]]-env.reference[:,12:]).abs().amax(-1),
            seconds=env.episode_length_buf*env.step_dt,roll=roll,pitch=pitch,yaw=yaw,
            mass=masses.sum(1),foot_jacobian=jac[:,jac_ids,:3,6:][:,:,:,env.joint_ids],
            gravity_joint=gravity[:,6:][:,env.joint_ids],kp=kp[:,env.joint_ids],kd=kd[:,env.joint_ids],
            soft_limits=d.soft_joint_pos_limits[:,env.joint_ids],friction=torch.minimum(
                torch.full_like(env.privileged[:,4],.6),.75*env.privileged[:,4]),targets=env.targets).items()}
        native_cpu=cpu(native);failure_cpu=cpu(env.failure)
        reasons_cpu={k:cpu(v) for k,v in env.failure_reasons.items()}
        records=[];success=torch.zeros_like(env.success);terminal=torch.zeros_like(env.success)
        timeout=(env.episode_length_buf>=env.max_episode_length)
        for i,c in enumerate(controllers):
            if finished[i]:continue
            state={k:buffers[k][i] for k in ('feet','forces','com','com_velocity','height','tilt',
                'root_velocity','angular_velocity','joint_position','joint_velocity','arm_error',
                'seconds','roll','pitch','yaw','mass','foot_jacobian','gravity_joint','kp','kd','soft_limits','friction')}
            outcome=c.update(state,bool(native_cpu[i]),buffers['targets'][i],env.step_dt)
            if failure_cpu[i] or outcome or timeout[i]:
                reasons=[k for k,v in reasons_cpu.items() if bool(v[i])]
                success[i]=bool(outcome=='success' and not failure_cpu[i] and not timeout[i])
                terminal[i]=bool(failure_cpu[i] or (outcome and not timeout[i]))
                records.append(dict(env=i,success=bool(success[i]),reason=','.join(reasons) or ('timeout' if timeout[i] else outcome),
                    seconds=float(state['seconds']),phase=c.phase,events=c.events,front_done=c.front_done,
                    final_metrics=c.metrics,native_ascent=c.native_ascent))
                finished[i]=True
                np.savez_compressed(output/f'exit_trace_{i:03d}.npz',**{k:np.asarray([r[k] for r in traces[i]]) for k in traces[i][0]})
                print(json.dumps(records[-1]),flush=True)
        env.success=success
        env.extras['episode_records']=records
        # Finished slots may auto-reset but are never counted or controlled again.
        return terminal,timeout
    env._get_dones=done
    return controllers

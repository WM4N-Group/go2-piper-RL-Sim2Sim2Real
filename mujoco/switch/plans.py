"""配置层：路线由任务列表组成。导航点是已知地图上的人工安全路点，无避障规划器。"""


def plan(scenario, staircase=None):
    if scenario=='box-stairs':
        c=staircase.config
        box_front=c.box_initial_front+c.push_distance
        return [dict(skill='nav',goal=[-.02,0.],surface_height=0.),
                dict(skill='push'),
                dict(skill='climb',surface='box',approach=[box_front-.83,0.]),
                dict(skill='nav',goal=[c.upper_front-.83,0.],surface_height=c.box_height),
                dict(skill='climb',surface='upper',approach=[c.upper_front-.83,0.]),
                dict(skill='nav',goal=[c.upper_front+1.5,0.],surface_height=c.upper_height)]
    if scenario == 'nav-nav':
        return [dict(skill='nav',goal=[0.,0.]),dict(skill='nav',goal=[.6,.7]),
                dict(skill='nav',goal=[1.4,.7])]
    if scenario == 'nav-climb':
        return [dict(skill='nav', goal=[-.08,0.]), dict(skill='climb')]
    if scenario == 'nav-push':
        return [dict(skill='nav', goal=[-.02,0.]), dict(skill='push')]
    return [dict(skill='nav', goal=[-.02,-2.]), dict(skill='push'),
            dict(skill='nav', goal=[-.4,-2.], yaw=3.141592653589793),
            dict(skill='nav', goal=[-.4,0.], yaw=0.),
            dict(skill='nav', goal=[-.08,0.]), dict(skill='climb')]

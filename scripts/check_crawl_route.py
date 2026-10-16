"""Independent geometry, terrain-clearance and retiming checks; no physics."""
import unittest
import numpy as np
import torch
from crawl_leg_kinematics import LegKinematics, rotate_vector
from plan_crawl_route import Geometry, foot_path, body_path, sampled_retime, smooth


class RouteChecks(unittest.TestCase):
    def test_world_kinematics_match_existing_usd_leg_model_with_yaw(self):
        geometry = dict(hip_origins=[[.1934,.0465,0],[.1934,-.0465,0],[-.1934,.0465,0],[-.1934,-.0465,0]],
                        hip_lateral_offsets=[.0955,-.0955,.0955,-.0955], link_lengths=[[.213,.213]]*4)
        old = LegKinematics(geometry, dtype=torch.float64)
        new = Geometry(geometry)
        poses = np.array([[1.2,-.3,.4,-.2,.1,.4],[-2.,1.1,.31,.15,-.1,-.5]])
        q = np.array([[[.2,.7,-1.7],[-.1,.8,-1.8],[.1,1.,-1.9],[-.2,.9,-1.6]]]*2)
        from scipy.spatial.transform import Rotation
        xyzw = Rotation.from_euler('xyz', poses[:,[4,3,5]]).as_quat()
        quaternion = torch.tensor(xyzw[:,[3,0,1,2]],dtype=torch.float64)
        expected = rotate_vector(quaternion[:,None],old.forward(torch.tensor(q)))+torch.tensor(poses[:,:3])[:,None]
        actual = new.forward(q,poses)
        np.testing.assert_allclose(actual,expected.numpy(),atol=1e-12)
        solved,_,_=new.inverse(actual,poses)
        np.testing.assert_allclose(solved,q,atol=1e-12)
        translation=np.array([8.,-5.,.2]); moved=poses.copy();moved[:,:3]+=translation
        np.testing.assert_allclose(new.inverse(actual+translation,moved)[0],q,atol=1e-12)

    def test_terrain_path_keeps_conservative_foot_sphere_outside_box(self):
        u=np.linspace(0,1,10001)
        for x in (.58,.65,.69):
            start=np.array([x,.16,.024]); target=np.array([.83,.16,.2245])
            path=foot_path(start,target,u)
            np.testing.assert_allclose(path[[0,-1]],[start,target],atol=1e-12)
            nearest=np.clip(path,[.75,-.6,0],[1.95,.6,.2])
            # The 22mm sphere with a2mm offset fits in this24mm envelope.
            self.assertGreaterEqual(np.linalg.norm(path-nearest,axis=1).min(),.024-1e-12)
            self.assertGreaterEqual(path[(path[:,0]>=.726)&(path[:,0]<=.774),2].min(),.2545-1e-12)
            eps=1e-5
            ends=foot_path(start,target,np.array([0,eps,1-eps,1]))
            self.assertLess(np.linalg.norm(ends[1]-ends[0])/eps,1e-7)
            self.assertLess(np.linalg.norm(ends[-1]-ends[-2])/eps,1e-7)

    def test_ground_arc_and_body_knots_are_continuous_with_rest_endpoints(self):
        u=np.linspace(0,1,1001)
        start=np.array([.1,.16,.024]);target=np.array([.3,.16,.024])
        path=foot_path(start,target,u)
        self.assertAlmostEqual(path[:,2].max(),.069)
        self.assertTrue((np.diff(path[:,0])>=0).all())
        knots=np.arange(24).reshape(4,6)*.01
        np.testing.assert_allclose(body_path(knots,np.linspace(0,1,4)),knots,atol=1e-12)
        for edge in (1/3,2/3):
            nearby=body_path(knots,np.array([edge-1e-5,edge,edge+1e-5]))
            self.assertLess(abs(np.diff(nearby,axis=0)).max(),1e-10)

    def test_retime_matches_analytic_quintic_limits_and_dense_replay(self):
        # For a unit quintic, max first derivative is1.875, second is10/sqrt(3).
        for delta in (.1,.7,1.5):
            u=np.linspace(0,1,385);q=(smooth(u)*delta)[:,None,None]
            result=sampled_retime(q)
            exact=max(1.875*delta/2.5,np.sqrt(10*delta/np.sqrt(3)/15))
            self.assertAlmostEqual(result['sampled_minimum_s'],exact,places=4)
            dense=np.linspace(0,1,10001)
            rate=30*dense**2*(1-dense)**2*delta/result['reserved_s']
            acc=60*dense*(1-dense)*(1-2*dense)*delta/result['reserved_s']**2
            self.assertLessEqual(abs(rate).max(),2.5)
            self.assertLessEqual(abs(acc).max(),15.)
        self.assertEqual(sampled_retime(np.zeros((385,4,3)))['reserved_s'],.02)


if __name__=='__main__':
    unittest.main()

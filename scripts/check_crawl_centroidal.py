"""Mathematical mass/force/torque checks, independent of an Isaac rollout."""
import unittest
import numpy as np
from crawl_centroidal import ArticulatedModel, three_contact_forces


def pendulum():
    eye=np.eye(3).tolist()
    return ArticulatedModel(dict(root='base',bodies=[dict(name='base',mass=2.,com=[0,0,0]),
        dict(name='rod',mass=3.,com=[.5,0,0]),dict(name='foot',mass=0.,com=[0,0,0])],
        joints=[dict(name='pitch',parent='base',child='rod',axis=[0,1,0],p0=[.2,0,0],p1=[0,0,0],r0=eye,r1=eye),
                dict(name='fixed',parent='rod',child='foot',axis=None,p0=[1.,0,0],p1=[0,0,0],r0=eye,r1=eye)]))


class CentroidalChecks(unittest.TestCase):
    def test_joint_motion_changes_com_and_gravity_torque_matches_potential_gradient(self):
        model=pendulum();q=np.array([[-.6],[0.],[.8]])
        p=np.zeros((3,3));quat=np.tile([1.,0,0,0],(3,1))
        state=model.forward(q,['pitch'],p,quat)
        expected=np.column_stack(((.2+.5*np.cos(q[:,0]))*3/5,np.zeros(3),-.5*np.sin(q[:,0])*3/5))
        np.testing.assert_allclose(state['com'],expected,atol=1e-12)
        torque=model.static_torque(state,['foot'],np.zeros((3,1,3)))[:,0]
        np.testing.assert_allclose(torque,-3*9.81*.5*np.cos(q[:,0]),atol=1e-12)
        eps=1e-6
        plus=model.forward(q+eps,['pitch'],p,quat)['com'][:,2]*5*9.81
        minus=model.forward(q-eps,['pitch'],p,quat)['com'][:,2]*5*9.81
        np.testing.assert_allclose(torque,(plus-minus)/(2*eps),atol=1e-8)
        # A force at the foot supplies the same upward moment as rod gravity.
        forces=np.zeros((3,1,3));forces[:,:,2]=3*9.81/2
        np.testing.assert_allclose(model.static_torque(state,['foot'],forces),0,atol=1e-12)

    def test_mixed_height_tripod_force_balance_and_outside_com_are_not_clamped(self):
        feet=np.array([[[.3,.2,.2],[.3,-.2,.2],[-.3,.2,0],[-.3,-.2,0]]])
        for leg in range(4):
            support=[i for i in range(4) if i!=leg]
            com=feet[:,support].mean(1);com[:,2]=.4
            force=three_contact_forces(feet,com,[20.],leg)
            np.testing.assert_allclose(force.sum(1),[[0,0,196.2]],atol=1e-12)
            np.testing.assert_allclose(np.cross(feet-com[:,None],force).sum(1),0,atol=1e-12)
            self.assertEqual(force[0,leg,2],0)
            self.assertTrue((force[0,support,2]>0).all())
        bad=three_contact_forces(feet,np.array([[2.,0.,.4]]),[20.],0)
        self.assertLess(bad[:,:,2].min(),0.)

    def test_base_only_mass_inference_preserves_other_bodies_and_rejects_invalid(self):
        model=pendulum();m=model.masses_from_total([4.,7.])
        np.testing.assert_allclose(m,[[1.,3.,0.],[4.,3.,0.]])
        with self.assertRaises(ValueError):model.masses_from_total([2.])
        with self.assertRaises(ValueError):model.masses_from_total([float('nan')])

    def test_tree_and_joint_column_validation(self):
        model=pendulum();data=model.data.copy();data['root']='missing'
        with self.assertRaises(KeyError):ArticulatedModel(data)
        with self.assertRaises(ValueError):model.forward(np.zeros((1,1)),['wrong'],[[0,0,0]],[[1,0,0,0]])

    def test_runtime_mass_override_is_explicit_named_and_does_not_mutate_usd_model(self):
        old=pendulum()
        new=old.with_runtime_properties(['foot','base','rod'],[1.,2.,3.],[[0,0,0],[0,0,0],[.5,0,0]])
        self.assertEqual(old.mass.sum(),5.)
        self.assertEqual(new.mass.sum(),6.)
        state=new.forward([[0.]],['pitch'],[[0,0,0]],[[1,0,0,0]])
        np.testing.assert_allclose(state['com'],[[(3*.7+1.2)/6,0,0]],atol=1e-12)
        with self.assertRaises(ValueError):old.with_runtime_properties(['base']*3,[1,2,3],np.zeros((3,3)))
        with self.assertRaises(ValueError):old.with_runtime_properties(old.names,[1,-1,2],np.zeros((3,3)))


if __name__=='__main__':unittest.main()

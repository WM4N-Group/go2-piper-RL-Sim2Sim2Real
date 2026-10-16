"""Articulated USD mass geometry and static load diagnostics (no simulator).

Static vertical contact allocation is a necessary-model diagnostic only: it omits
acceleration, angular momentum, impact, frictional forces and motor temperature.
"""
import copy
import numpy as np
from scipy.spatial.transform import Rotation


class ArticulatedModel:
    def __init__(self, data):
        self.data = data
        self.names = [b['name'] for b in data['bodies']]
        self.body_index = {name: i for i, name in enumerate(self.names)}
        self.mass = np.array([b['mass'] for b in data['bodies']])
        self.local_com = np.array([b['com'] for b in data['bodies']])
        self.root = self.body_index[data['root']]
        self.joint_names = [j['name'] for j in data['joints'] if j['axis'] is not None]
        self.joint_index = {name: i for i, name in enumerate(self.joint_names)}
        pending = list(data['joints']); ordered = []; known = {data['root']}
        while pending:
            available = [j for j in pending if j['parent'] in known]
            if not available:
                raise ValueError('Joint tree is cyclic or disconnected')
            for j in available:
                if j['child'] in known:
                    raise ValueError('Joint tree has multiple parents')
                ordered.append(j); known.add(j['child']); pending.remove(j)
        if known != set(self.names):
            raise ValueError('Every rigid body must be reachable from the root')
        self.ordered = ordered
        self.descendant = np.zeros((len(self.joint_names), len(self.names)), dtype=bool)
        ancestors = {data['root']: []}
        for j in ordered:
            chain = ancestors[j['parent']]+([self.joint_index[j['name']]] if j['axis'] is not None else [])
            ancestors[j['child']] = chain
            self.descendant[chain, self.body_index[j['child']]] = True

    @classmethod
    def from_usd(cls, path):
        from pxr import Usd, UsdPhysics
        stage = Usd.Stage.Open(str(path))
        if stage is None:
            raise ValueError('Could not open USD')
        bodies = []
        for prim in stage.Traverse():
            if not prim.HasAPI(UsdPhysics.RigidBodyAPI):
                continue
            mass = float(prim.GetAttribute('physics:mass').Get())
            com = np.array(prim.GetAttribute('physics:centerOfMass').Get(), dtype=float)
            if mass < 0 or not np.isfinite(mass):
                raise ValueError('Authored finite masses required')
            if mass == 0:
                com = np.zeros(3)  # Massless end-effector has authored -inf COM.
            if not np.isfinite(com).all():
                raise ValueError('A massive body has no finite authored COM')
            bodies.append(dict(name=prim.GetName(), mass=mass, com=com.tolist()))
        joints = []
        def frame(prim, side):
            q = prim.GetAttribute('physics:localRot'+side).Get()
            quat = [*q.GetImaginary(), q.GetReal()]
            return (list(prim.GetAttribute('physics:localPos'+side).Get()),
                    Rotation.from_quat(quat).as_matrix().tolist())
        for prim in stage.Traverse():
            if not prim.IsA(UsdPhysics.Joint):
                continue
            parent = prim.GetRelationship('physics:body0').GetTargets()
            child = prim.GetRelationship('physics:body1').GetTargets()
            if len(parent) != 1 or len(child) != 1:
                raise ValueError('Only unanchored tree articulations are supported')
            if prim.IsA(UsdPhysics.RevoluteJoint):
                axis = np.eye(3)['XYZ'.index(prim.GetAttribute('physics:axis').Get())].tolist()
            elif prim.IsA(UsdPhysics.FixedJoint):
                axis = None
            else:
                raise ValueError('Unsupported joint type')
            p0, r0 = frame(prim, '0'); p1, r1 = frame(prim, '1')
            joints.append(dict(name=prim.GetName(), parent=parent[0].name, child=child[0].name,
                               axis=axis, p0=p0, r0=r0, p1=p1, r1=r1))
        roots = set(b['name'] for b in bodies)-set(j['child'] for j in joints)
        if len(roots) != 1:
            raise ValueError('Expected one floating root')
        return cls(dict(root=roots.pop(), bodies=bodies, joints=joints))

    def masses_from_total(self, totals):
        """Only valid for the audited task's base-only additive randomization."""
        totals = np.atleast_1d(totals).astype(float)
        masses = np.tile(self.mass, (len(totals), 1))
        masses[:, self.root] += totals-self.mass.sum()
        if not np.isfinite(masses).all() or (masses < 0).any():
            raise ValueError('Invalid inferred masses')
        return masses

    def with_runtime_properties(self, body_names, nominal_masses, local_centers):
        """Use observed PhysX mass properties; USD zero mass is not always massless."""
        if len(set(body_names)) != len(body_names) or set(body_names) != set(self.names):
            raise ValueError('Runtime rigid bodies do not match the USD tree')
        masses, centers = np.asarray(nominal_masses), np.asarray(local_centers)
        if (masses.shape != (len(body_names),) or centers.shape != (len(body_names),3)
                or not np.isfinite(masses).all() or not np.isfinite(centers).all()
                or (masses < 0).any() or masses.sum() <= 0):
            raise ValueError('Invalid runtime mass properties')
        data = copy.deepcopy(self.data)
        for body in data['bodies']:
            i = body_names.index(body['name'])
            body['usd_authored_mass'] = body['mass']
            body['usd_authored_com'] = body['com']
            body['mass'] = float(masses[i]); body['com'] = centers[i].tolist()
        data['mass_property_source'] = 'Observed initialized PhysX nominal masses and local COM positions'
        return ArticulatedModel(data)

    def forward(self, q, names, root_position, root_quaternion_wxyz, masses=None):
        q = np.asarray(q, dtype=float)
        if q.ndim != 2 or q.shape[1] != len(names) or len(set(names)) != len(names):
            raise ValueError('Expected uniquely named joint columns')
        indices = {name: i for i, name in enumerate(names)}
        if not set(self.joint_names).issubset(indices):
            raise ValueError('Missing joint positions')
        n = len(q); count = len(self.names)
        position = np.empty((n, count, 3)); orientation = np.empty((n, count, 3, 3))
        position[:, self.root] = root_position
        orientation[:, self.root] = Rotation.from_quat(np.asarray(root_quaternion_wxyz)[:, [1,2,3,0]]).as_matrix()
        axes = np.zeros((n, len(self.joint_names), 3)); origins = axes.copy()
        for j in self.ordered:
            parent, child = self.body_index[j['parent']], self.body_index[j['child']]
            joint_rot = orientation[:, parent] @ np.array(j['r0'])
            joint_pos = position[:, parent]+np.einsum('nij,j->ni', orientation[:, parent], j['p0'])
            if j['axis'] is None:
                motion = np.eye(3)
            else:
                ji = self.joint_index[j['name']]
                axes[:, ji] = np.einsum('nij,j->ni', joint_rot, j['axis'])
                origins[:, ji] = joint_pos
                motion = Rotation.from_rotvec(q[:, indices[j['name']], None]*np.array(j['axis'])).as_matrix()
            orientation[:, child] = joint_rot @ motion @ np.array(j['r1']).T
            position[:, child] = joint_pos-np.einsum('nij,j->ni', orientation[:, child], j['p1'])
        body_com = position+np.einsum('nbij,bj->nbi', orientation, self.local_com)
        masses = np.broadcast_to(self.mass, (n,count)) if masses is None else np.broadcast_to(masses, (n,count))
        if not np.isfinite(masses).all() or (masses < 0).any() or (masses.sum(1) <= 0).any():
            raise ValueError('Expected finite positive total mass')
        com = (body_com*masses[:,:,None]).sum(1)/masses.sum(1)[:,None]
        return dict(position=position, orientation=orientation, body_com=body_com, com=com,
                    axes=axes, origins=origins, masses=masses)

    def static_torque(self, state, foot_names, forces_world):
        """Actuator torques for gravity plus specified static point-contact forces."""
        n = len(state['com']); torque = np.zeros((n, len(self.joint_names)))
        gravity = np.zeros_like(state['body_com']); gravity[:,:,2] = -9.81*state['masses']
        foot_ids = [self.body_index[name] for name in foot_names]
        for j in range(len(self.joint_names)):
            arm = state['body_com']-state['origins'][:,j,None]
            moment = (np.cross(arm, gravity)*self.descendant[j][None,:,None]).sum(1)
            contact_arm = state['position'][:,foot_ids]-state['origins'][:,j,None]
            moment += (np.cross(contact_arm, forces_world)*self.descendant[j,foot_ids][None,:,None]).sum(1)
            torque[:,j] = -(moment*state['axes'][:,j]).sum(1)
        return torque


def three_contact_forces(feet, com, total_mass, swing_leg):
    """Unique vertical static forces; preserve negative forces to flag infeasibility."""
    legs = [i for i in range(4) if i != swing_leg]
    relative = feet[:,legs,:2]-com[:,None,:2]
    matrix = np.stack((np.ones_like(relative[:,:,0]),relative[:,:,0],relative[:,:,1]),axis=1)
    rhs = np.zeros((len(com),3));rhs[:,0] = np.asarray(total_mass)*9.81
    forces = np.zeros_like(feet)
    forces[:,legs,2] = np.linalg.solve(matrix,rhs[...,None])[...,0]
    return forces

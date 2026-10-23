"""按仿真时钟录制；仅 --video 时创建渲染器，不控制交互窗口相机。"""
import imageio.v2 as imageio
import mujoco


class VideoRecorder:
    def __init__(self, model, path, fps=25):
        self.renderer = mujoco.Renderer(model, height=540, width=960)
        self.writer = imageio.get_writer(str(path), fps=fps, codec='libx264', macro_block_size=2)
        self.interval, self.next_frame = 1./fps, 0.
        self.camera = mujoco.MjvCamera()
        self.camera.distance, self.camera.azimuth, self.camera.elevation = 4., 130., -30.

    def capture(self, data, camera=None):
        if data.time+1e-8 < self.next_frame:
            return
        self.camera.lookat[:] = data.qpos[:3]
        self.renderer.update_scene(data, camera=camera if camera is not None else self.camera)
        self.writer.append_data(self.renderer.render())
        self.next_frame += self.interval

    def close(self):
        try:
            self.writer.close()
        finally:
            self.renderer.close()

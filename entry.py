from planner import Planner
from perceptor import Perceptor
from executor import Executor
from prompts import Prompt
import erniebot
import cv2
import os
import time
import threading
from utils import VLM
from speech2text import speech2text

from core.realsense2 import *
from core.wrap_xarm import xarm6
from core.calibrate import Calibration

robot = xarm6()  # robot
realcam = Realsense2()  # camera


def capture_and_save():
    # 获取当前时间
    start_time = time.time()

    # 设置图像保存间隔（秒）
    save_interval = 0.5

    for img in realcam:
        # 逐帧捕获图像
        rgb_img, _, _ = img  # rgb图，深度图，深度信息

        # 显示当前帧
        cv2.imshow('camera', rgb_img)

        # 获取当前时间
        current_time = time.time()

        # 检查是否到达保存时间间隔
        if current_time - start_time >= save_interval:
            cv2.imwrite(f"camera_output/output.jpg", rgb_img)
            # 更新开始时间
            start_time = current_time

    cv2.destroyAllWindows()


# 创建并启动捕获和保存图像的线程
capture_thread = threading.Thread(target=capture_and_save)
capture_thread.start()

if __name__ == '__main__':

    planner = Planner()
    perceptor = Perceptor(VLM())
    executor = Executor()
    prompts = Prompt()

    # robot.move_init_pose()  # 初始位姿

    # 获取标定数据
    cal_data = np.load(f'core/data.npy', allow_pickle=True).item()
    RT_cam2gri = cal_data['RT_cam2gripper']
    RT_cam2gri[:3, 3] *= 1000
    RT_obj2cam = np.identity(4)
    RT_gri2base = np.identity(4)

    # task_instruction = "Please tell me how to reach the red bus."
    task_instruction = speech2text()
    VLM_scene_description = None
    flag = 1

    while True:

        # 保存到特定路径下
        scene_path = f'camera_output/output.jpg'

        # 轮询等待图片保存好
        while not os.path.exists(scene_path):
            time.sleep(0.5)
            pass

        # print(realcam)

        # TEST
        # obj_list = perceptor.detect_obj_list(scene_path)
        # obj_list

        if flag == 1:
            VLM_scene_description = perceptor.generate_scene_description(
                img_path=scene_path,
                task_instruction=task_instruction)

            flag = 0

        print("Scene Description: \n")
        print(VLM_scene_description)

        obj_info = perceptor.detect_obj_list(scene_path)
        objects = perceptor.obj_list
        print(f"Objects: {objects}")

        obj_info1 = obj_info[0]
        x1, y1 = obj_info1['box']['top_left']
        x2, y2 = obj_info1['box']['bottom_right']

        print('sssss')
        print(
            x1 + (x2-x1)/2,
            y1 - (y1-y2)/2
        )

        goal = prompts.generate_llm_prompt(query=task_instruction,
                                           objects=objects,
                                           desc=VLM_scene_description)
        print("Planer's input prompt: ")
        print(goal)

        meta_actions = planner.respond_human_request(goal)
        print("Meta actions: ")
        print(meta_actions)

        execution_message = planner.meta_action_to_func_call(meta_actions)

        VLM_scene_description = perceptor.generate_scene_description(
            img_path=scene_path,
            task_instruction=task_instruction)

        planner.dialog_mem_between_LLM_and_human.append(
            {'role': 'user',  # 成功执行后，如果尚未完整最终目标，告诉LLM当前的场景描述进入下一轮决策
             'content': "Execute successfully! Current scene on the table: " + VLM_scene_description})

        response = erniebot.ChatCompletion.create(
            model=planner.llm,
            messages=planner.dialog_mem_between_LLM_and_human,
        )  # response: you need to tell me the color of the bottle

        print(response.get_result())
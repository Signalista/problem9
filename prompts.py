class Prompt:
    def __init__(self):
        # #  TODO: VLM 返回给 LLM 的场景描述的细粒度应该匹配task instruction, 比如感兴趣objects之间的方位。
        pass

    def generate_llm_prompt(self, query, objects, desc):
        """initial the prompt for LLM

        Args:
            query (str): the user's request
            objects (list): objects can be seen on the table.
            desc (str): a description of current scene on table from VLM
        """
        # initial prompt of llm, including role description, available tools and some notice.
        llm_instruction = """You are a helpful assistant that pays attention to the user's instructions and excels at fulfilling the user's request by operating a robot arm in a tabletop environment.
        Pay attention to the relationships between objects, including: On, Under, Right, Front, Left, Behind, Next-to, In.
        To achieve this, you can use the following tools:
        1. Pick(object): Pick out the object. For example, executing Pick(apple), the robot arm will go to where the apple is and pick it up. 
        2. Move(relation, reference_object): move to the specified position. For example, executing Move(left, banana), the robot arm will move to the left of the banana. 
        3. Place(relation, reference_object): move to the specified position to place the picked object. For example, executing Place(left, banana), the robot arm will move to the left of the banana and place the picked object there. 
        Here are some examples of decomposing a user's request:
        1. objects = [blue block, yellow block, mug]
        User: place the blue block on the yellow block.
        Agent should decompose it into these several steps: Pick(blue block), Place(On, yellow block).
        2. objects = [hand, mouse, bottle]
        User: shake hand with me.
        Agent should move to where the hand is: Move(Next-to, hand).
        Notice:
        1. Single Action Rule: Execute only ONE action at a time. After receiving the observation from its execution, you may proceed with another action. 
        2. DO NOT GENERATE ANYTHING THAT IS NOT SEEN IN THE TABLE.
        WHEN TO STOP:
        When the current scene matches the user's request, you must finally answer with DONE.
        """

        # one-shot demonstration for llm
        llm_one_shot = [
            """Current scene on the table: There are an apple, a banana and a mug on the table. Objects: [apple, banana, mug]. The user's request: Pick up the apple and place it to the left of the banana.""",
            """Thought: I need to firstly pick up the apple.
            Action: Pick(apple)""",
            """Observation: Execute successfully! Current scene on the table: There are a banana and a mug. Objects: [banana, mug].""",
            """Thought: I have grasped the apple, so next I just need to place it to the left of the banana.
            Action: Place(Left, banana)""",
            """Observation: Execute successfully! Current scene on the table: There is an apple to its right a banana, and also a mug. Objects: [apple, banana, mug].""",
            """Thought: I have fulfilled the user's request. DONE."""
        ]

        # follow the format of {"role": "**", "content": "**"}
        # messages = [{"role": "user", "content": llm_instruction}]
        messages = f"user: {llm_instruction}\n"
        messages += "assistant: I've understood your instruction, start please.\n"
        for idx, shot in enumerate(llm_one_shot):
            if idx % 2 == 0:
                messages += f"user: {shot}"
            else:
                messages += f"assistant: {shot}"
        messages += f"user: Current scene on the table: {desc}. Objects: {objects}. The user's request: {query}."

        return messages

    def vlm_desc_prompt(self, task_instruction):
        # 生成场景描述的prompt
        # guide the vlm to decribe the scene and response with expected format.
        prompt = """You are an expert excels at describing the scene you see. 
        For example, if user's request is to pick up the apple and place it to the left of the banana.
        A good scene description could be There is an apple on the middle of the table, a banana on its left side, and a mug on the right bottom corner of the table.
        Notice:
        1. Pay attention to the position relationships between objects, including: On, Under, Right, Front, Left, Behind, Next-to, In.
        2. You should consider the user's request to give a informative and targeted scene description (You do not need to answer the request itself).
        Here is the request from the user: """
        prompt += task_instruction
        return prompt

    # def vlm_determine_prompt():
    #     # 判断是否完成任务
    #     pass

    def vlm_detect_prompt(self, specific_object=None):
        # 返回物体坐标的prompt
        if specific_object:
            if isinstance(specific_object, str):
                prompt = f"""You are an expert excels at detecting objects. Please detect {specific_object} and answer its/their box coordinates. For example, {"object": []}."""
            elif isinstance(specific_object, list):
                prompt = f"""You are an expert excels at detecting objects. Please detect the following types of objects: {specific_object}. Answer their box coordinates. For example, {"object1": [], "object2": [], ...}."""
            else:
                print("The input type is not supported.")
        else:
            prompt = """You are an expert excels at detecting objects. Please detect all the major objects and answer with a dict containing their box coordinates. For example, {"object1": [], "object2": [], ...}."""
        return prompt


if __name__ == '__main__':
    # test generate_llm_prompt()
    import erniebot

    erniebot.api_type = "aistudio"
    erniebot.access_token = "2f486dfb4e1511984e187e18de9d84dc641a2132"
    model = 'ernie-3.5'
    prompt = Prompt().generate_llm_prompt(query="Pick up the mouse and place it to the right of the bottle.",
                                          objects=['bottle', 'mouse', 'key'],
                                          desc="There are a bottle, a mouse, and a key on the table.")
    history = prompt
    response = erniebot.ChatCompletion.create(
        model=model,
        messages=prompt
    )

    while not 'DONE' in response.get_result():
        history.append({"role": "assistant", "content": response.get_result()})
        print(response.get_result())
        user_response = input("User: ")  # imitating the user's reply
        history.append({"role": "user", "content": user_response})
        response = erniebot.ChatCompletion.create(
            model=model,
            messages=history
        )

    print(response.get_result())

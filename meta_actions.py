# 这里定义 meta action
def Pick(object):
    """Pick out the object. For example, executing Pick(apple), the robot arm will go to where the apple is and pick it up.

    Args:
        object (str): the target object to pick up
    """
    # TODO
    pass


def Move(relation, reference_object):
    """Move to the specified position. For example, executing Move(left, banana), the robot arm will move to the left of the banana.

    Args:
        relation (str): the position relationship between target object and reference object
        reference_object (str): a reference object
    """
    # TODO
    pass


def Place(relation, reference_object):
    """Move to the specified position and place the picked object there.

    Args:
        relation (str): the position relationship between target object and reference object
        reference_object (str): a reference object
    """
    # TODO
    pass

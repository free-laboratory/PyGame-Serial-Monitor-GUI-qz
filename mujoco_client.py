import roslibpy

_ros = None
_joint_topic = None
_cartesian_topic = None


def _ensure_ros():
    global _ros, _joint_topic, _cartesian_topic

    if _ros is not None and _ros.is_connected:
        return

    _ros = roslibpy.Ros(host='127.0.0.1', port=9090)
    _ros.run()

    _joint_topic = roslibpy.Topic(
        _ros,
        '/gui/joint_targets',
        'std_msgs/Float64MultiArray'
    )

    _cartesian_topic = roslibpy.Topic(
        _ros,
        '/gui/cartesian_delta',
        'std_msgs/Float64MultiArray'
    )


def send_joint_positions(joints):
    _ensure_ros()
    _joint_topic.publish(roslibpy.Message({
        'data': list(joints)
    }))


def send_cartesian_delta(delta):
    _ensure_ros()
    _cartesian_topic.publish(roslibpy.Message({
        'data': list(delta)
    }))
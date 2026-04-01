import roslibpy

_ros = roslibpy.Ros(host='127.0.0.1', port=9090)
_ros.run()

_topic = roslibpy.Topic(
    _ros,
    '/gui/joint_targets',
    'std_msgs/Float64MultiArray'
)

def send_joint_positions(joints):
    _topic.publish(roslibpy.Message({
        'data': list(joints)
    }))
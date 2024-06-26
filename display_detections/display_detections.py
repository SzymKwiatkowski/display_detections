#!/usr/bin/env python
import sys

import cv2
import cv_bridge
import message_filters
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import QoSReliabilityPolicy
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray

class DisplayDetectionNode(Node):

    def __init__(self):
        super().__init__('display_detections')

        self._bridge = cv_bridge.CvBridge()

        output_image_qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            reliability=QoSReliabilityPolicy.RELIABLE,
            depth=1)

        self._image_pub = self.create_publisher(Image, '~/detection_image', output_image_qos)

        self._image_sub = message_filters.Subscriber(self, Image, '~/image')
        self._detections_sub = message_filters.Subscriber(self, Detection2DArray, '~/detections')

        self._synchronizer = message_filters.ApproximateTimeSynchronizer(
            (self._image_sub, self._detections_sub), 5, 0.01)
        self._synchronizer.registerCallback(self.on_detections)

    def on_detections(self, image_msg, detections_msg):
        cv_image = self._bridge.imgmsg_to_cv2(image_msg)

        # Draw boxes on image
        for detection in detections_msg.detections:
            max_class = None
            max_score = 0.0
            for result in detection.results:
                hypothesis = result.hypothesis
                if hypothesis.score > max_score:
                    max_score = hypothesis.score
                    max_class = hypothesis.class_id
            if max_class is None:
                print("Failed to find class with highest score", file=sys.stderr)
                return

            cx = detection.bbox.center.position.x
            cy = detection.bbox.center.position.y
            sx = detection.bbox.size_x
            sy = detection.bbox.size_y

            min_pt = (round(cx - sx / 2.0), round(cy - sy / 2.0))
            max_pt = (round(cx + sx / 2.0), round(cy + sy / 2.0))
            color = (0, 255, 0)
            thickness = 2
            cv2.rectangle(cv_image, min_pt, max_pt, color, thickness)

            label = '{} {:.3f}'.format(max_class, max_score)
            pos = (min_pt[0], max_pt[1])
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(cv_image, label, pos, font, 0.75, color, 1, cv2.LINE_AA)
            
        detection_image_msg = self._bridge.cv2_to_imgmsg(cv_image, encoding=image_msg.encoding)
        detection_image_msg.header = image_msg.header

        self._image_pub.publish(detection_image_msg)

def main():
    rclpy.init()
    rclpy.spin(DisplayDetectionNode())
    rclpy.shutdown()

if __name__ == '__main__':
    main()
import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose

def get_shoulder_points(image_path):
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    with mp_pose.Pose(static_image_mode=True) as pose:
        results = pose.process(img_rgb)
        if not results.pose_landmarks:
            return None, None

        landmarks = results.pose_landmarks.landmark
        h, w, _ = img.shape

        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]

        left_shoulder_xy = (int(left_shoulder.x * w), int(left_shoulder.y * h))
        right_shoulder_xy = (int(right_shoulder.x * w), int(right_shoulder.y * h))

        return left_shoulder_xy, right_shoulder_xy

def apply_clothes(person_img_path, clothes_img_path):
    person_img = cv2.imread(person_img_path)
    clothes_img = cv2.imread(clothes_img_path, cv2.IMREAD_UNCHANGED)  # 保留透明度通道

    left_shoulder, right_shoulder = get_shoulder_points(person_img_path)

    print("左肩膀:", left_shoulder)
    print("右肩膀:", right_shoulder)

    if left_shoulder is None or right_shoulder is None:
        print("沒偵測到肩膀點")
        return person_img

    shoulder_width = right_shoulder[0] - left_shoulder[0]
    print("肩膀寬度:", shoulder_width)

    if shoulder_width <= 0:
        print("肩膀寬度 <= 0，無法換衣")
        return person_img

    # 調整衣服寬度與肩膀寬度相同，高度按比例縮放
    h_c, w_c = clothes_img.shape[:2]
    new_w = shoulder_width
    scale_ratio = new_w / w_c
    new_h = int(h_c * scale_ratio)

    if new_w <= 0 or new_h <= 0:
        print("計算出來的衣服尺寸不合理")
        return person_img

    clothes_img = cv2.resize(clothes_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 讓衣服居中於肩膀寬度，x座標往左移動半個肩膀寬度
    x_offset = left_shoulder[0] - new_w // 2
    # 衣服y座標往上調整0.3倍衣服高度，使衣服掛在肩膀上方
    y_offset = left_shoulder[1] - int(new_h * 0.3)

    # 邊界限制，避免負數座標
    x_offset = max(0, x_offset)
    y_offset = max(0, y_offset)

    y1, y2 = y_offset, y_offset + new_h
    x1, x2 = x_offset, x_offset + new_w

    # 如果超出圖片範圍，調整邊界與衣服區域大小
    if y2 > person_img.shape[0]:
        y2 = person_img.shape[0]
        y1 = y2 - new_h
    if x2 > person_img.shape[1]:
        x2 = person_img.shape[1]
        x1 = x2 - new_w

    # 重新計算衣服的範圍（裁切因邊界限制）
    clothes_y1 = 0 if y_offset >= 0 else abs(y_offset)
    clothes_y2 = clothes_y1 + (y2 - y1)
    clothes_x1 = 0 if x_offset >= 0 else abs(x_offset)
    clothes_x2 = clothes_x1 + (x2 - x1)

    # 合成衣服透明度 (BGR + alpha)
    alpha_s = clothes_img[clothes_y1:clothes_y2, clothes_x1:clothes_x2, 3] / 255.0
    alpha_l = 1.0 - alpha_s

    for c in range(3):  # BGR通道
        person_img[y1:y2, x1:x2, c] = (alpha_s * clothes_img[clothes_y1:clothes_y2, clothes_x1:clothes_x2, c] +
                                       alpha_l * person_img[y1:y2, x1:x2, c])

    return person_img

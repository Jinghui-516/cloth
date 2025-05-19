from flask import Flask, render_template, request
from virtual_try_on import apply_clothes
import os
import cv2

app = Flask(__name__)

# 確保 static 資料夾存在
os.makedirs('static', exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        person_file = request.files['person']
        clothes_file = request.files['clothes']

        person_path = 'static/person.jpg'
        clothes_path = 'static/clothes.png'
        output_path = 'static/result.jpg'

        person_file.save(person_path)
        clothes_file.save(clothes_path)

        result_img = apply_clothes(person_path, clothes_path)
        cv2.imwrite(output_path, result_img)

        return render_template('index.html', result_image=output_path)

    return render_template('index.html', result_image=None)

if __name__ == '__main__':
    app.run(debug=True)

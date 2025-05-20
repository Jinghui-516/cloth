import requests
from bs4 import BeautifulSoup

import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

from flask import Flask, render_template, request,json,make_response, jsonify
from datetime import datetime, timezone, timedelta
import google.generativeai as genai
app = Flask(__name__)

@app.route("/")
def index():
    homepage = "<h1>楊靖惠Python網頁(Firestore py) 電影分級查詢a</h1>"
    homepage += "<a href=/mis>MIS</a><br>"
    homepage += "<a href=/today>顯示日期時間</a><br>"
    homepage += "<a href=/welcome?nick=jhyang&work=pu>傳送使用者暱稱</a><br>"
    homepage += "<a href=/account>網頁表單傳值</a><br>"
    homepage += "<a href=/rwd>靖惠簡介網頁</a><br>"
    homepage += "<br><a href=/read>讀取Firestore資料</a><br>"
    homepage += "<a href=/spider>擷取開眼即將上映電影，存到資料庫</a><br>"
    homepage += "<a href=/searchQ>輸入關鍵字查詢電影</a><br>"
    homepage += "<br><a href=/traffic>臺中市114年01月份十大易肇事路段(口)</a><br>"
    homepage += "<a href=/rate>擷取開眼即將上映電影(含分級及最新更新日期)，存到資料庫</a><br>"

    homepage +='<script src="https://www.gstatic.com/dialogflow-console/fast/messenger/bootstrap.js?v=1"></script>'
    homepage +='<df-messenger '
    homepage +='intent="WELCOME" '
    homepage +='chat-title="jinghui(楊靖惠)" '
    homepage +='agent-id="323b3ad9-a66f-4639-842b-6b65c8c68f68" '
    homepage +='language-code="zh-tw" '
    homepage +='></df-messenger>'
    
    return homepage


@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1>"

@app.route("/today")
def today():
    tz = timezone(timedelta(hours=+8))
    now = datetime.now(tz)
    return render_template("today.html", datetime = str(now))

@app.route("/rwd")
def rwd():
    return render_template("rwd.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("nick")
    w = request.values.get("work")
    return render_template("welcome.html", name=user,work=w)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.order_by("lab").get()    
    for doc in docs:         
        Result += "文件內容：{}".format(doc.to_dict()) + "<br>"    
    return Result






@app.route("/spider")
def spider():
    db = firestore.client()

    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".filmListAllX li")
    for item in result:
 
        i = item.find("img")
        a = item.find("a")
        r = item.find(class_="runtime")
  

        pos = r.text.find("片長")
        pos2 = r.text.find("分")
        movieL = "無"
        if (pos>0):
            movieL = r.text[pos+3 : pos2 +1]

        doc = {
            "title": i.get("alt"),
            "picture": i.get("src"),
            "hyperlink": "https://www.atmovies.com.tw" + a.get("href"),
            "showDate":r.text[5:15],
            "showLength":movieL
        }
        id = a.get("href")[7:19]

        doc_ref = db.collection("電影").document(id)
        doc_ref.set(doc)
    return "電影資料庫更新"

@app.route("/search")
def search():
    info = ""
    db = firestore.client()  
    docs = db.collection("電影").get() 
    for doc in docs:
        if "" in doc.to_dict()["title"]:
            info += "片名：<a href=" + doc.to_dict()["hyperlink"] +">" +doc.to_dict()["title"] + "</a><br>" 
            info += "海報：<img src=" + doc.to_dict()["picture"] + "></img><br>"
            info += "片長：" + doc.to_dict()["showLength"] + " <br>" 
            info += "上映日期：" + doc.to_dict()["showDate"] + "<br><br>"           
    return info

@app.route("/searchQ", methods=["POST","GET"])
def searchQ():
    if request.method == "POST":
        MovieTitle = request.form["MovieTitle"]
        info = ""
        db = firestore.client()     
        collection_ref = db.collection("電影")
        docs = collection_ref.order_by("showDate").get()
        for doc in docs:
            if MovieTitle in doc.to_dict()["title"]: 
                info += "片名：<a href=" + doc.to_dict()["hyperlink"] +">" +doc.to_dict()["title"] + "</a><br>" 
                info += "海報：<img src=" + doc.to_dict()["picture"] + "></img><br>"
                info += "片長：" + doc.to_dict()["showLength"] + " <br>" 
                info += "上映日期：" + doc.to_dict()["showDate"] + "<br><br>"            
        return info


    else:
        return render_template("input.html")





@app.route("/traffic", methods=["GET", "POST"])
def traffic():
    result = []
    if request.method == "POST":
        keyword = request.form["keyword"]
        url = "https://datacenter.taichung.gov.tw/swagger/OpenData/b9c9b28d-847c-489d-ba60-94f8728910b9"
        try:
            response = requests.get(url, verify=False)  # 忽略 SSL 憑證
            JsonData = response.json()

            for item in JsonData:
                if "路口名稱" in item and keyword in item["路口名稱"]:
                    result.append({
                        "路口名稱": item["路口名稱"],
                        "總件數": item.get("總件數", "無資料"),
                        "主要肇因": item.get("主要肇因", "無資料")
                    })
        except Exception as e:
            return f"⚠️ 查詢失敗：{e}"
    return render_template("traffic.html", result=result)

@app.route("/rate")
def rate():
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".filmListAllX li")
    lastUpdate = sp.find(class_="smaller09").text[5:]

    for x in result:
        picture = x.find("img").get("src").replace(" ", "")
        title = x.find("img").get("alt")    
        movie_id = x.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw" + x.find("a").get("href")

        t = x.find(class_="runtime").text
        showDate = t[5:15]

        showLength = ""
        if "片長" in t:
            t1 = t.find("片長")
            t2 = t.find("分")
            showLength = t[t1+3:t2]

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": showLength,
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("電影含分級").document(movie_id)
        doc_ref.set(doc)
    return "近期上映電影已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate



@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    # fetch queryResult from json
    action =  req.get("queryResult").get("action")
    #msg =  req.get("queryResult").get("queryText")
    #info = "動作：" + action + "； 查詢內容：" + msg
    if (action == "rateChoice"):
        rate =  req.get("queryResult").get("parameters").get("rate")
        info = "您選擇的電影分級是：" + rate + "，相關電影：\n"

        db = firestore.client()
        collection_ref = db.collection("電影含分級")
        docs = collection_ref.get()
        result = ""
        for doc in docs:
            dict = doc.to_dict()
            if rate in dict["rate"]:
                result += "片名：" + dict["title"] + "\n"
                result += "介紹：" + dict["hyperlink"] + "\n\n"
        if result =="":
            result = "抱歉，資料庫目前無您要查詢分級的電影"
        info += result

    elif (action == "MovieDetail"):
        FilmQ =  req.get("queryResult").get("parameters").get("FilmQ")
        keyword =  req.get("queryResult").get("parameters").get("any")
        #info = "您詢問的問題是" + FilmQ +"，關鍵字是:" +keywork

        if (FilmQ == "片名"):
            db = firestore.client()
            collection_ref = db.collection("電影含分級")
            docs = collection_ref.get()
            found = False
            info = ""
            for doc in docs:
                dict = doc.to_dict()
                if keyword in dict["title"]:
                    found = True 
                    info += "片名：" + dict["title"] + "\n"
                    info += "海報：" + dict["picture"] + "\n"
                    info += "影片介紹：" + dict["hyperlink"] + "\n"
                    info += "片長：" + dict["showLength"] + " 分鐘\n"
                    info += "分級：" + dict["rate"] + "\n" 
                    info += "上映日期：" + dict["showDate"] + "\n\n"
            if not found:
                info += "很抱歉，目前無符合這個關鍵字的相關電影喔"

    elif (action == "CityWeather"):
        city =  req.get("queryResult").get("parameters").get("city")
        token = "rdec-key-123-45678-011121314"
        url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=" + token + "&format=JSON&locationName=" + str(city)
        Data = requests.get(url)
        Weather = json.loads(Data.text)["records"]["location"][0]["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
        Rain = json.loads(Data.text)["records"]["location"][0]["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
        MinT = json.loads(Data.text)["records"]["location"][0]["weatherElement"][2]["time"][0]["parameter"]["parameterName"]
        MaxT = json.loads(Data.text)["records"]["location"][0]["weatherElement"][4]["time"][0]["parameter"]["parameterName"]
        info = city + "的天氣是" + Weather + "，降雨機率：" + Rain + "%"
        info += "，溫度：" + MinT + "-" + MaxT + "度"


    return make_response(jsonify({"fulfillmentText": "這是楊靖惠的程式回覆，" + info}))

@app.route("/AI")
def AI():
    api_key = 'AIzaSyCmes_DnpDmKibXW0TycVe--xcyowTDHiE'
    genai.configure(api_key = api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content('我想查詢靜宜大學資管系的評價？')
    return response.text


if __name__ == "__main__":
    app.run(debug=True)
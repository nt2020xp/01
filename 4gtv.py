from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import cloudscraper
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import urllib.parse

app = FastAPI()

def encrypt_data(data, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(data.encode(), AES.block_size)
    return base64.b64encode(cipher.encrypt(padded_data))

def decrypt_data(encrypted_data, key, iv):
    decipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(decipher.decrypt(base64.b64decode(encrypted_data)), AES.block_size)
    return decrypted_data.decode()

@app.get("/4gtv/{channel_id}")
async def get_playlist(channel_id: str):
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get('https://api2.4gtv.tv/Channel/GetChannel/'+channel_id)
        response.raise_for_status()  # 检查请求是否成功

        data = json.loads(response.text)["Data"]
        cno = data["fnID"]
        cid = data["fs4GTV_ID"]

        jarray = {
            "fnCHANNEL_ID": cno,
            "fsASSET_ID": cid,
            "fsDEVICE_TYPE": "mobile",
            "clsIDENTITY_VALIDATE_ARUS": {"fsVALUE": ""}
        }
        abc = json.dumps(jarray)

        key = b"ilyB29ZdruuQjC45JhBBR7o2Z8WJ26Vg"
        iv = b"JUMxvVMmszqUTeKn"
        enc = encrypt_data(abc, key, iv)

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        p = "value=" + urllib.parse.quote_plus(enc.decode())

        post_response = scraper.post('https://api2.4gtv.tv//Channel/GetChannelUrl3', data=p, headers=headers)
        post_response.raise_for_status()

        resp_data = json.loads(post_response.text)["Data"]
        decrypted_data = decrypt_data(resp_data, key, iv)
        playlist = json.loads(decrypted_data)["flstURLs"][0]
        return RedirectResponse(url=playlist, status_code=302)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

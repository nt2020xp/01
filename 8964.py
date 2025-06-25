from flask import Flask, request, Response
import time

app = Flask(__name__)

channels = {
    '4gtv-4gtv072': ['TVBS新聞', 1, 2],
    '4gtv-4gtv152': ['東森新聞', 1, 6],
    '4gtv-4gtv153': ['東森財經', 1, 2],
    'litv-ftv13': ['民視新聞', 1, 6],
    '4gtv-4gtv009': ['中天新聞', 2, 7],
    '4gtv-4gtv052': ['華視新聞', 1, 2],
    '4gtv-4gtv074': ['中視新聞', 1, 2],
    '4gtv-4gtv051': ['台視新聞', 1, 2],
    '4gtv-4gtv056': ['台視財經', 1, 2],
    'litv-longturn14': ['寰宇新聞', 4, 2],
    '4gtv-4gtv156': ['寰宇台灣', 1, 6],
    '4gtv-4gtv158': ['寰宇財經', 5, 2],
    '4gtv-4gtv010': ['非凡新聞', 1, 6],
    '4gtv-4gtv048': ['非凡商業', 1, 2],
    '4gtv-4gtv041': ['華視', 1, 8],
    '4gtv-4gtv040': ['中視', 1, 8],
    '4gtv-4gtv066': ['台視', 1, 2],
    '4gtv-4gtv155': ['民視', 1, 6],
    'litv-ftv07': ['民視旅遊台', 1, 6],
    '4gtv-4gtv076': ['亞洲旅遊台', 1, 2],
    'litv-longturn19': ['Smart知識台', 5, 6],
    '4gtv-4gtv047': ['靖天日本台', 1, 8],
    '4gtv-4gtv062': ['靖天育樂台', 1, 8],
    '4gtv-4gtv055': ['靖天映畫台', 1, 8],
    '4gtv-4gtv063': ['靖天國際台', 1, 6],
    '4gtv-4gtv065': ['靖天資訊台', 1, 8],
    '4gtv-4gtv061': ['靖天電影台', 1, 7],
    '4gtv-4gtv046': ['靖天綜合台', 1, 8],
    '4gtv-4gtv058': ['靖天戲劇台', 1, 8],
    '4gtv-4gtv054': ['靖天歡樂台', 1, 8],
    '4gtv-4gtv045': ['靖洋戲劇台', 1, 8],
    '4gtv-4gtv044': ['靖天卡通台', 1, 8],
    '4gtv-4gtv057': ['靖洋卡通台', 1, 8],
    'litv-longturn03': ['龍華電影台', 5, 2],
    'litv-longturn02': ['龍華洋片台', 5, 2],
    'litv-longturn21': ['龍華經典台', 5, 2],
    'litv-longturn11': ['龍華日韓台', 5, 2],
    'litv-longturn12': ['龍華偶像台', 5, 2],
    'litv-longturn18': ['龍華戲劇台', 5, 6],
    'litv-longturn01': ['龍華卡通台', 1, 2],
    '4gtv-4gtv073': ['TVBS', 1, 2],
    '4gtv-4gtv067': ['TVBS精采台', 1, 8],
    '4gtv-4gtv068': ['TVBS歡樂台', 1, 7],
    '4gtv-4gtv034': ['八大精彩台', 1, 6],
    '4gtv-4gtv039': ['八大綜藝台', 1, 7],
    '4gtv-4gtv064': ['中視菁采台', 1, 8],
    '4gtv-4gtv080': ['中視經典台', 1, 6],
    '4gtv-4gtv109': ['中天亞洲台', 1, 6],
    '4gtv-4gtv001': ['民視台灣台', 1, 6],
    '4gtv-4gtv003': ['民視第一台', 1, 6],
    '4gtv-4gtv004': ['民視綜藝台', 1, 8],
    'litv-ftv09': ['民視影劇台', 1, 2],
    '4gtv-4gtv049': ['采昌影劇台', 1, 8],
    '4gtv-4gtv042': ['公視戲劇', 1, 6],
    'litv-longturn22': ['台灣戲劇台', 5, 2],
    '4gtv-4gtv011': ['影迷數位電影台', 1, 6],
    '4gtv-4gtv013': ['視納華仁紀實頻道', 1, 6],
    '4gtv-4gtv070': ['愛爾達娛樂台', 1, 7],
    '4gtv-4gtv018': ['達文西頻道', 1, 8],
    'litv-ftv15': ['影迷數位紀實台', 1, 7],
    '4gtv-4gtv006': ['豬哥亮歌廳秀', 1, 9],
    '4gtv-4gtv014': ['時尚運動X', 1, 5],
    '4gtv-4gtv043': ['客家電視台', 1, 9],
    '4gtv-4gtv053': ['GINX Esports TV', 1, 8],
    '4gtv-4gtv059': ['CLASSICA 古典樂', 1, 6],
    '4gtv-4gtv077': ['TRACE Sport Stars', 1, 2],
    '4gtv-4gtv079': ['ARIRANG阿里郎頻道', 1, 2],
    '4gtv-4gtv082': ['TRACE Urban', 1, 6],
    '4gtv-4gtv083': ['Mezzo Live HD', 1, 6],
    '4gtv-4gtv110': ['Pet Club TV', 1, 2],
    '4gtv-4gtv084': ['國會頻道1台', 1, 6],
    '4gtv-4gtv085': ['國會頻道2台', 1, 5],
    '4gtv-4gtv101': ['智林體育台', 1, 5],
    '4gtv-4gtv102': ['東森購物1台', 1, 6],
    '4gtv-4gtv103': ['東森購物2台', 1, 6],
    '4gtv-4gtv104': ['第1商業台', 1, 7],
    'litv-ftv03': ['VOA美國之音', 1, 7],
    'litv-ftv10': ['半島國際新聞台', 1, 7],
    'litv-ftv16': ['好消息', 1, 2],
    'litv-ftv17': ['好消息2台', 1, 2],
    'litv-longturn04': ['博斯魅力台', 5, 6],
    'litv-longturn05': ['博斯高球台', 5, 2],
    'litv-longturn06': ['博斯高球二台', 5, 2],
    'litv-longturn07': ['博斯運動一台', 5, 2],
    'litv-longturn08': ['博斯運動二台', 5, 2],
    'litv-longturn09': ['博斯網球台', 5, 2],
    'litv-longturn10': ['博斯無限台', 5, 2],
    'litv-longturn13': ['博斯無限二台', 4, 2],
    'litv-longturn20': ['ELTV生活英語台', 5, 6],
    '4gtv-4gtv016': ['韓國娛樂台 KMTV', 5, 6]
}

@app.route('/litv')
def litv():
    base_url = request.base_url
    channel_id = request.args.get('id')

    if not channel_id:
        return Response(
            '\n'.join(f"{data[0]},{base_url}?id={cid}" for cid, data in channels.items()),
            mimetype='text/plain; charset=utf-8'
        )

    if channel_id not in channels:
        msg = ["頻道不存在，可用頻道列表："]
        msg += [f"{data[0]},{base_url}?id={cid}" for cid, data in channels.items()]
        return Response('\n'.join(msg), status=404, mimetype='text/plain; charset=utf-8')

    video_param = channels[channel_id][1]
    audio_param = channels[channel_id][2]
    timestamp = int(time.time() / 4 - 355017625)
    t = timestamp * 4

    m3u8 = "#EXTM3U\r\n"
    m3u8 += "#EXT-X-VERSION:3\r\n"
    m3u8 += "#EXT-X-TARGETDURATION:4\r\n"
    m3u8 += f"#EXT-X-MEDIA-SEQUENCE:{timestamp}\r\n"

    for _ in range(3):
        m3u8 += "#EXTINF:4,\r\n"
        m3u8 += (
            f"https://ntd-tgc.cdn.hinet.net/live/pool/{channel_id}/litv-pc/"
            f"{channel_id}-avc1_6000000={video_param}-mp4a_134000_zho={audio_param}-"
            f"begin={t}0000000-dur=40000000-seq={timestamp}.ts\r\n"
        )
        timestamp += 1
        t += 4

    return Response(
        m3u8,
        mimetype='application/vnd.apple.mpegurl',
        headers={
            "Content-Disposition": f'inline; filename="{channel_id}.m3u8"',
            "Content-Length": str(len(m3u8))
        }
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

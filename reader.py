import multiprocessing
import m3u8
import requests

completed = []

movie_name = "Anyone.But.You"
m3_file = "dest\Anyone.But.You\dfda;15a3873cfa10585daa846515d1b0ea069138af455cb8a8ee490165a0a7.m3u8"

def get(url):
    r = requests.get(url)
    if r.status_code != 200:
        raise requests.HTTPError(r)
    return r

def init_download(url):
    response = get(url)

    if url in completed:
        return split_url

    split_url = url.split('/')
    with open("dest/" + movie_name + "/" + split_url[-1], 'wb') as file:
        file.write(response.content)

    return url

def download_complete(url):
    if url not in completed:
        completed.append(url)
    print("Done: ", url)

def download_failed(url):
    print("Failed: ", url)


if __name__ == "__main__": 
# Load the M3U8 playlist file
    playlist = m3u8.load(m3_file)

    pool = multiprocessing.Pool(4)
    i = 0
    for item in playlist.data['segments']:
        i += 1
        url = item['uri']
        if url in completed:
            continue
        pool.apply_async(init_download, (url,), callback=download_complete, error_callback=download_failed)

    pool.close()
    pool.join()
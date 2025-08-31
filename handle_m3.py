import asyncio
import os
import requests
import m3u8
import multiprocessing
import signal
from urllib.parse import urlparse
import time

SESSION = requests.session()
HEADERS = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    'Accept': "application/json, text/javascript, */*; q=0.01",
    'method': "GET",
}

SESSION.headers.update(HEADERS)

def signal_handler(sig, frame):
    print("Exiting...")
    exit()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def request(url):
    retries = 0
    while retries < 3:
        try:
            r = SESSION.get(url, timeout=30)  # Adjust timeout as per your needs
            r.raise_for_status()  # Raise HTTPError for bad status codes
            return r
        except Exception as err:
            print(f"\033[31mOther error occurred: {err}")
            retries += 1
            if retries < 3:
                print(f"\033[33mRetrying ({retries}/{3})...")
                time.sleep(5)  # Wait for a moment before retrying
            else:
                raise  # If retries exceeded, raise the exception for handling at higher level

    raise RuntimeError(f"\033[31mFailed to retrieve data from {url} after {3} retries")


class Handle:

    # initializer
    def __init__(self, args):
        self.threads = 6 # default download threads at 10
        self.root_ = ""
        self.master_ = args['url']
        self.filename = args['filename']
        self.base_id = ""
        self.target_m3u8 = ""
        self.completed = []
        self.failed = []
        self.total_files = 0
        self.temp_container = []
        self.headers = {
            'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        }

    def setHeaders(self):
        parsed_url = urlparse(self.master_)
        self.headers = {
            'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            'Host': parsed_url.netloc
        }

    def mirror_content(self, url):
        try: 
            content = request(url)
            return 200, url, content.content
        except Exception as e:
            print(f"@ mirror_content: {e}")
            return 500, url, ""

    def init_download(self, url, count):
        # check if the file exist in the folder to skip
        exist = self.check_downloaded(url)
        if exist:
            self.completed.append(url)
            return url, count
        
        temp_url = url

        # check if url is complete
        if "https://" in url: # is complete url
            temp_url = url
        else: # is not complete url
            temp_url = self.root_ + "/" + url

        status, filename, content = self.mirror_content(temp_url)

        if (status == 500):
            self.failed.append(url)
            return url, count
        
        filename = filename.split("/")
        filename = filename[-1]

        with open('dest/'+self.filename+"/"+filename, 'wb') as file:
            file.write(content)
        
        self.completed.append(filename)

        return url, count
    
    def check_downloaded(self, url):
        folder_path = 'dest/' + self.filename

        # Create the full path to the file
        full_path = os.path.join(folder_path, url)

        # Check if the file exists
        if os.path.exists(full_path):
            return True
        else:
            return False

    def download_complete(self, result):
        url, count = result
        item_done = url.split('/')
        self.completed.append(url)
        self.progress(len(self.completed) + len(self.failed), self.total_files, item_done[-1])

    def download_failed(self, e):
        try:
            raise e
        except Exception:
           print(f"Download failed: {e}")
           exit()
    
    # processes
    async def start(self):
        # get the root url first
        self.set_root()
        # print("ROOT: ", self.root_)

        os.makedirs("dest/" + self.filename, exist_ok=True)

        self.setHeaders()
        # print('@HEADERS', self.headers)

        # search for the m3u8 for the highest quality
        m3u8 = self.get_target_m3u8(self.master_)

        print("Download started...")
        self.start_handling(m3u8)
        print("Done.")

        with open('failed.txt', 'w') as file:
            for line in self.failed:
                file.write(" ".join(line) + "\n")
        
        return self.target_m3u8 # return this to have a reference name for the m3u8 local file

    def process_master_list(self, data):
        temp = 0
        current_link = ""
        print("@process_master_list", data)
        for item in data:
            current = item['stream_info']['resolution'].split('x')
            current = int(current[1])
            if current > temp:
                temp = current
                current_link = item['uri']
        self.set_base_data(current_link)
        return current_link # video m3u8 link and resolution

    def get_target_m3u8(self, url):
        # print('@get_target_m3u8', url)
        response = request(url)
        m3 = m3u8.loads(response.text)

        current_quality = None
        temp_bandwidth = 0

        # pick the highest quality
        for item in m3.data['playlists']:
            temp_bandwidth = item['stream_info']['bandwidth'] # set the current bandwidth
            if current_quality == None: # set initial if currently no value
                current_quality = item
            if temp_bandwidth > current_quality['stream_info']['bandwidth']: # check if temp is greater than previous
                current_quality = item # set as the current highest quality

        print(f"Current quality: {current_quality['stream_info']['resolution']}")

        if current_quality == None: 
            self.create_reference(response.text, "head.m3u8", "w")
            return m3u8.loads(response.text)

        print(current_quality['uri'])
        
        # check if link is complete or sub
        if "https://" not in current_quality['uri']:
            # transform the master url to array
            temp_master_uri = self.master_.split("/")
            if ("tmstr" in self.master_):
                # get the domiain
                domain = temp_master_uri[:3]
                temp_uri = '/'.join(domain)
                current_quality['uri'] = temp_uri + current_quality['uri']
            else:
                # replace the last part by the actual target from the m3u8
                temp_master_uri[-1] = current_quality['uri']
                # reconstruct the link
                current_quality['uri'] = '/'.join(temp_master_uri)


        response = request(current_quality['uri'])
        self.create_reference(response.text, "head.m3u8", "w")
        return m3u8.loads(response.text)

    def create_reference(self, data, filename, mode):
        file = "dest/" + self.filename + "/" +filename
        with open(file, mode) as file:
            file.write(data)

    def start_handling(self, m3):
        m3_data = m3.data

        self.total_files = len(m3_data['segments'])

        self.progress(0, self.total_files, "initialize...")
        pool = multiprocessing.Pool(self.threads)
        i = 0
        for item in m3_data['segments']:
            i += 1
            url = item['uri']
            if url in self.completed:
                continue
            pool.apply_async(self.init_download, (url, i), callback=self.download_complete, error_callback=self.download_failed)
        
        pool.close()
        pool.join()
        
    def progress(self, progress, ceiling, item_done):
        percent = 100 * (progress / ceiling)
        bar = '█' * int(percent) + '-' * (100 - int(percent))
        print(f"\r\033[32m|{bar}| {percent:.2f}% | Item: {item_done}", end="\r")

    def set_base_data(self, url):
        print("@set_base_data ",url)
        temp = url.split('/')
        # self.base_id = temp[0]
        self.target_m3u8 = "head.m3u8"

    def set_root(self):
        url = self.master_ # get a copy of the master url
        string_array = url.split('/') # transform into array
        print(string_array)
        string_array.pop() # removes the https
        string_array.pop(0) # removes the empty
        string_array.pop(0) # remove the last part to make it the universal link to append the non-link references

        self.root_ = "https://"+ "/".join(string_array)


async def main():
    handle = Handle(args={
        'url':'https://yvwjo.mv25d5lb1.online/_v2p-dvbo/12a3c523f3105800ed8c394685aeeb0b9b2eaa5c1eb0e0ef4c047baea93ece832257df1a4b6125fcfa38c35da05dee86aad28d46d73fc4e9d4e5a53b5270f0d5749544f8594fea0d5691a6b03e157b162631822f454760c8d1c6fb0fcff42fc42a10b9160c69bb09ba/h/list;15a3873cfa10585daa846515d1b0ea069138af455cb8a8ee490165a0a7.m3u8',
        'subtitle': False,
        'filename': 'Lady.Bird'
    })
    await handle.start()

if __name__ == "__main__":

    asyncio.run(main())


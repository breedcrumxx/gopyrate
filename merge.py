from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
import os
import subprocess
import glob

class Merge:
    def __init__(self, data):
        self.filename = data['filename'] + ".mp4"
        self.reference_path = "dest/" + data['filename']
        self.save_point = ""
        self.path = self.filename

    def run(self):
        m3u8 = self.get_reference()

        with open(m3u8, 'r') as file:
            contents = file.readlines()

        with open(self.reference_path+'/reference.m3u8', 'w') as file:
            for item in contents:
                if "https://" in item or "http://" in item:
                    stripped = item.split("/")
                    file.write(stripped[-1])
                    continue
                file.write(item)

        self.merge()

    def merge(self):

        m3u8 = self.get_reference()

        with open(m3u8, 'r') as file:
            contents = file.readlines()

        with open(self.reference_path+'/reference.m3u8', 'w') as file:
            for item in contents:
                if "https://" in item or "http://" in item:
                    stripped = item.split("/")
                    file.write(stripped[-1])
                    continue
                file.write(item)

        ffmpeg_command = ["ffmpeg",
               "-loglevel", "warning",
               "-allowed_extensions", "ALL",
               "-i", self.reference_path+'/reference.m3u8',
               "-acodec", "copy",
               "-vcodec", "copy",
               "-bsf:a", "aac_adtstoasc",
               self.save_point+self.path]

        # execute the command
        subprocess.run(ffmpeg_command)

        print("Merging done.")
        print(f"File {self.filename} is now ready! ")
        return True
    
    async def start(self):

        m3u8 = self.get_reference()

        with open(m3u8, 'r') as file:
            contents = file.readlines()

        with open(self.reference_path+'/reference.m3u8', 'w') as file:
            for item in contents:
                if "https://" in item or "http://" in item:
                    stripped = item.split("/")
                    file.write(stripped[-1])
                    continue
                file.write(item)

        ffmpeg_command = ["ffmpeg",
               "-loglevel", "warning",
               "-allowed_extensions", "ALL",
               "-i", self.reference_path+"/reference.m3u8",
               "-acodec", "copy",
               "-vcodec", "copy",
               "-bsf:a", "aac_adtstoasc",
               self.save_point+self.path]

        # execute the command
        subprocess.run(ffmpeg_command)

        print("Merging done.")
        print(f"File {self.filename} is now ready! ")
        return True
    
    def get_reference(self):

        with open("config.txt", 'r') as file:
            key, self.save_point = file.readline().split("=")

        txt_files = glob.glob(os.path.join(self.reference_path, '*.m3u8'))
        print(txt_files, self.reference_path)
        
        if not txt_files: 
            print("@GET REFERENCE: Missing reference file.")
            exit(0)

        return txt_files[0]

# separate execution if the automatic failed during runtime.
if __name__ == "__main__":

    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-u", "--url", default="", help="The url of the movie.")
    parser.add_argument("-n", "--name", default="", help="The filename to save.")

    args = vars(parser.parse_args())

    data = {
        'filename': args['name'],
        'url': ''
    }

    merge = Merge(data=data)

    merge.run()

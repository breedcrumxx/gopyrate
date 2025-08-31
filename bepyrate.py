from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
import shutil
# from playwright.async_api import async_playwright
import asyncio
from handle_m3 import Handle
from merge import Merge
from cleaner import Cleaner
import json
import winsound

import time
import os
import sys

traffic = []
results = []

def clean_cache(folder):
    # clear the files 
    # ignore if -safe is enabled
    # clear txt files
    # clear dest folder
    for file_or_folder in os.listdir(folder):
        file_or_folder_path = os.path.join(folder, file_or_folder)
        try:
            if os.path.isfile(file_or_folder_path):
                os.remove(file_or_folder_path)
            elif os.path.isdir(file_or_folder_path):
                shutil.rmtree(file_or_folder_path)
        except Exception as e:
            print(f"Error deleting {file_or_folder_path}: {e}")



async def trigger(page):
        print('APPENDING ELEMENT')
        await page.evaluate('''
            var elemDiv = document.createElement('div');
            elemDiv.style.cssText = 'position:absolute;width:100%;height:100%;opacity:0.3;z-index:100;background:#000;';
            elemDiv.classList.add('m3u8-found')
            document.body.appendChild(elemDiv)
        ''')

async def filter_result(page, result, data): # filter only targets from network traffic
    try:
        # print(result) # testing
        traffic.append(result)
        with open('logs.txt', 'w') as logs:
            for item in traffic:
                logs.write(str(item) + '\n')
        if ("list;" in result.url and ".m3u8" in result.url) or "list;" in result.url: # append the link of m3u8 
            print(result.url)
            results.append({'label': 'm3u8', 'url': result.url})
            await trigger(page)

    except:
        pass

async def response_handler(page, response):
    try:
        body = await response.body()
        body_text = body.decode('utf-8')
        print(body_text) # testing
        traffic.append(response)
        with open('logs.txt', 'w') as logs:
            for item in traffic:
                logs.write(str(item) + '\n')
    except:
        pass

async def simulate_click(page):
    await page.evaluate('''
        $('.singlemv:contains(#BackUp)').click()''')

async def handle_new_tab(page, event): # to close unwanted tabs
    await page.context.pages[1].close()

async def attempt_remove_ads(page):
    await page.evaluate(r'''
        items = document.querySelectorAll("a[target='_blank']")
        items.forEach(elem => {
            elem.parentElement.style.height = "1px"
            elem.parentElement.style.with = "1px"
        }) ''')
    
async def check_new_page(page):
    clean_a_tags = r'''
        const element = document.querySelector('div.btn-watchnow');
        if (element) {
            element.click();
        }
    '''

    # # Execute the JavaScript and get the coordinates
    await page.evaluate(clean_a_tags)

async def run(data, flags):
    # async with async_playwright() as pw:
    # global results  # Declare results as global to modify the global results array
    # results = []  # Reset results array
    
    # browser = await pw.firefox.launch(headless=False) # headless temporary
    # context = await browser.new_context()
    # await context.grant_permissions(['notifications']) # to remove notification popups
    # # page = await browser.new_page()

    # # create a new page in a pristine context.
    # page = await context.new_page()

    # await page.set_viewport_size({"width": 500, "height": 500})

    # page.on('popup', lambda event: handle_new_tab(page, event)) # handle unwanted new tabs
    # page.on("request", lambda request: filter_result(page, request, data)) # handle request
    # # page.on('requestfinished', lambda event: check_new_page(page))
    # # page.on('response', lambda response: response_handler(page, response))

    # # website execution
    # await page.goto(data['url'], timeout=30000)
    # clean_a_tags = r'''
    #     const element = document.querySelector('div.auto-play');
    #     element.click();
    # '''

    # # # Execute the JavaScript and get the coordinates
    # if (flags['auto']):
    #     await page.evaluate(clean_a_tags)

    # print("Waiting for the files to be found...")

    # try:
    #     check = page.wait_for_selector('div.m3u8-found')
    #     # Wait for the condition to be met, and set a timeout if needed
    #     await asyncio.wait_for(check, timeout=60000)  # Wait for 2mins

    #     # Your code to do something with the element when it's found
    # except asyncio.TimeoutError:
    #     print("Timeout: The condition was not met within the specified timeout.")

    # await page.close()
    # await browser.close()
    # keep this line for future use.
    # await page.screenshot(path="screenshot.png", full_page=True)
    
    # close all connections 

    # to record the download time span
    start_time = time.perf_counter()

    target_data = {
        'url': data['url'],
        'subtitle': "",
        'sub_link': '',
        'filename': data['filename']
    }

    # if data['start'] and data.get('season'):
    #     target_data['filename'] = data['filename'] + ".S" + "%02d"% + int(data['season']) + "E" + "%02d"% +  int(data['start'])

    target = Handle(target_data)
    await target.start()

    end_time = time.perf_counter()

    # download time span
    download_span = end_time - start_time

    # # track merging speed
    # merge the files into specified file name and extension (.mp4 .mkv .mov)

    merge_files = Merge(target_data)

    start_time = time.perf_counter()

    await merge_files.start()

    end_time = time.perf_counter()

    # merging time span
    merging_span = end_time - start_time

    # download_min, download_sec = divmod(download_span, 60)
    merging_min, merging_sec = divmod(merging_span, 60)
    downloading_min, downloading_sec = divmod(download_span, 60)
    
    print(f"""
        Downloading took: {int(downloading_min)} minutes, {downloading_sec:.2f} seconds
        Merging took: {int(merging_min)} minutes, {merging_sec:.2f} seconds
    """)

    return
    if not flags['safe']: # if safe mode is disabled, it will clean all the files in the folder
        clean_cache("dest/"+target_data['filename'])


    # if start < end:
    #     data['url'] = data['url'][:-1] + str(start + 1)
    #     data['start'] = "" + str(start + 1)
    #     # data['filename'] = data['filename'][:-1] + str(start + 1)
    #     await run(data)

def help():
    print()
    print("Alpha test of BePyrate v0.4.1-alpha")
    print()
    print("Execution instructions")
    print("python bepyrate.py followed by parameters: ")
    print("-u, --url | followed by your movie link.")
    print("-s, --subtitle | to enable download of the subtitle.")
    print("-o, --output | followed by the name example (Movie.1) Please use period instead of spaces.")
    print("-safe, --safe-mode | to disable auto cleaning of cache.")
    print("-m, --merge | to run re-merge of previous failed run. (-m -o filename)")
    print("-d, --delete | to delete all cache files.")
    print("-c, --commands | to show all commands.")
    print("-a, --auto | turn auto off.")
    print()
    print("WHATS NEW!")
    print("* SERIES DOWNLOADER")
    print("* DIRECTORY SPECIFIER")
    print("HOW TO USE?")
    print()
    print("-dir, --directory | specify the directory where to store the downloaded movie, it will create the directory if it doesn't exist.")
    print("-sr, --series | range e.g. 1-20 | this will download the episode 1 to 20.")
    print("You can specify the start and end of the series, e.g. 2-5.")
    print()
    print("Currently built for M4UFREE.TV and FMOVIES")
    print()
    print("Developer@DanRosete")
    print()


# Function to read the ref file as download list
def prepare_targets(args):
    print("Task: Reading reference file...")
    targets = []

    if args['url'] == None: # if it's type of series download

        ref_file = "ref.txt" if args['series'] else args['series']

        with open("config.txt", 'r') as file:
            key, save_point = file.readline().split("=")

        # read the ref file
        # check if the ref file exist
        if os.path.isfile(ref_file):
            with open(ref_file, 'r') as file:
                contents = file.readlines()
                if len(contents) == 0: # exit if the file doesnt have anything
                    print(f"Reference file named ({args['series']}) doesn't contain anything, exiting...")
                    exit()

                for content in contents:
                    [filename, link] = content.split(' ')

                    if not os.path.isfile(save_point+filename+".mp4"):
                        targets.append({
                            "url": link,
                            "filename": filename
                        })

        else: 
            print(f"Reference ({args['series']}) doesn't exist, please create it in the root folder!")
            exit()
    else: # if it's not type of series download
        targets.append({
            "url": args['url'],
            "filename": args['output']
        })
    return targets
    

if __name__ == "__main__":
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-u", "--url", help="The url of the movie.")
    parser.add_argument("-o", "--output", default="sample.mp4", type=str, help="Output filename.")
    parser.add_argument("-sr", "--series", type=str, default="ref.txt", help="Supply the text file name containing the download links and filenames.")
    parser.add_argument("-dir", "--directory", default="", type=str, help="Specify the destination.")
    parser.add_argument("-safe", "--safe", action='store_true', help="Output filename.")
    parser.add_argument("-m", "--merge", action='store_true', help="Output filename.")
    parser.add_argument("-c", "--commands", action='store_true')
    parser.add_argument("-d", "--delete", action='store_true')

    args = vars(parser.parse_args())

    if args['delete']:
        print("Deleting all the cache files...")
        clean_cache('dest')
        print("Done!")
        sys.exit()

    if args['commands']:
        help()
        sys.exit()

    if args['merge']:
        # if we just want to merge an old file in the cache folder
        # # track merging speed
        start_time = time.perf_counter()
        # merge the files into specified file name and extension (.mp4 .mkv .mov)
        merge_files = Merge({"filename": args['output']})
        merge_files.merge()

        end_time = time.perf_counter()

        # merging time span
        merging_span = end_time - start_time
        merging_min, merging_sec = divmod(merging_span, 60)
        print(f"""
            Merge execution time: {int(merging_min)} minutes, {merging_sec:.2f} seconds
        """)

        if not args['safe']:
            clean_cache('/dest/'+args['output'])
    else:

        directory = ''

        # if the directory flag is enabled, check if the directory exist under the save_point
        if args['directory']:
            directory = args["directory"] + '/'
            with open("config.txt", 'r') as file:
                key, save_point = file.readline().split("=")
                if not os.path.exists(save_point+directory): # if the directory doesn't exist, then create the folter
                    os.mkdir(save_point+directory)

        targets = prepare_targets(args)
        flags = {
            'safe': args['safe'],
        }

        for i, target in enumerate(targets):
            print(f"\033[32mTask: Starting {i+1}/{len(targets)}...")
            print(f"\033[36mTitle: {target['filename']}")
            asyncio.run(run(target, flags))

    # Notify on script finished execution
    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)   

#     # Alpha test of BePyrate v1.0.0-alpha
#     #
#     # execution instructions
#     # python bepyrate.py followed by parameters
#     # - Quality -
#     # -h high or 1080p
#     # -m mid or 720p
#     # -l low or 480p
#     #     
#     # - Subtitles -
#     # enable subtitle download -s
#     #
#     # Current Features
#     # paste and download
#     # with subtitles
#     # loseless file format
#     #
#     # Currently built for M4UFREE.TV 
#     #
#     # Developer@DanRosete

#     # v1.2.0-alpha
#     # enable auto generate of title -at
#     # enable auto generate of title for series -ats


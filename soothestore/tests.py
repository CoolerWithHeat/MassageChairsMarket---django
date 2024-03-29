import asyncio
import aiohttp
import time,  requests

# request = requests.get("http://localhost/GetProduct/5/")
# print(request.json())

async def fetch(url, session):
    try:
        start_time = time.time()
        async with session.get(url) as response:
            status_code = response.status
            text = await response.text()
            end_time = time.time()
            duration = end_time - start_time
            return status_code, text, duration
    except aiohttp.ClientError as e:
        return 500, str(e), None

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(url, session) for url in urls]
        return await asyncio.gather(*tasks)

tries = 0
if __name__ == "__main__":
    urls = ["http://172.206.235.69/Buy/"] * 1999
    while True:
        try:
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(fetch_all(urls))
            total_duration = 0
            for status_code, result, duration in results:
                print("Status code:", status_code)
                if (status_code == 500):
                    print(result)
                if duration:
                    rounded_duration = round(duration, 1)
                    print("Request duration:", rounded_duration, "seconds")
                    total_duration += duration
            if total_duration:
                average_duration = round(total_duration / len(results), 1)
                print("Average request duration:", average_duration, "seconds")
            print(f"Trial {tries} Done waiting for second")
            tries += 1
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("Interrupted by user. Exiting...")
            break
        except Exception as e:
            print("An error occurred:", e)
            print("Continuing...")
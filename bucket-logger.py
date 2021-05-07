import asyncio
import websockets
import json
import argparse
import schedule
import datetime

# Connect to this host
ws_host = 'wss://ws-beta.nanoticker.info'
# logging accounts with a certain rep
repCheck = ['nano_1repnode4qpnebqobohfaxcgbrhtumfs6emijugpdkrcxb3jettdaw95xwio','nano_1json51qn9t7cqebcds1b7f9t3cffbki7qanudqpo67xcpowpt1org1p9rus','nano_1a59d7z7r5mtoeqb96ssy14igg9rjaree1zcaeqestf7y9fondqxj43gtcyf','nano_3faucet4t1nnru6yra9iioia76jddur6zqg6d3fp7h1soyyd8qhgx6tizrsy']
# Number of seconds between each logging
interval = 5

print ("Counting buckets")
counter = {}
counterReps = {repCheck[0][:12]:0, repCheck[1][:12]:0, repCheck[2][:12]:0, repCheck[3][:12]:0}

def printCounter():
    global counter
    global counterReps
    print(counter)
    print(counterReps)
    #Append stats to file or create new file
    try:
      with open('buckets.json', 'a') as outfile:
        outfile.write(str(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')) + ': %r\n' %counter)
      with open('reps.json', 'a') as outfile:
        outfile.write(str(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')) + ': %r\n' %counterReps)

    except Exception as e:
      print('Could not save json file. Error: %r' %e)
      return
    
schedule.every(interval).seconds.do(printCounter)

def pretty(message):
    return json.dumps(message, indent=2)

async def main():
    global counter
    global counterReps
    # Predefined subscription message
    msg = {
        "action": "subscribe",
        "topic": "confirmation"
    }
    try:
        async with websockets.connect(ws_host) as websocket:
            await websocket.send(json.dumps(msg))
            while 1:
                rec = json.loads(await websocket.recv())
                #print(rec['message']['block']['representative'])
                
                bucket = 0
                balance = int(rec['message']['block']['balance'])
                while balance > 0:
                    balance >>= 1
                    bucket += 1
                
                if (bucket in counter):
                    counter[bucket] += 1
                else:
                    counter[bucket] = 1
                    
                # check reps
                for rep in repCheck:
                    if (rep == rec['message']['block']['representative']):
                        counterReps[rep[:12]] += 1
                    
    except Exception as e:
        print(e)
        # wait 5sec and reconnect
        await asyncio.sleep(5)
        await main()

async def counterTask():
  while 1:
    schedule.run_pending()
    await asyncio.sleep(0.01)

futures = [main(), counterTask()]
loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(asyncio.wait(futures))
except KeyboardInterrupt:
    pass

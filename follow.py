import requests
import json
from multiprocessing.pool import ThreadPool
import time
import random


def follow_user(token):
    time.sleep(random.randint(0, 3))
    try:
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json; charset=utf-8",
                   "User-Agent": "okhttp/4.2.2",
                   "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",
                   "Authorization": "OAuth " + token,
                   "X-Device-ID": "3ee667f50affd197"
                   }
        # Unfollow
        # data = {"operationName":"FollowButton_UnfollowUser","variables":{"input":{"targetID":target_id}},"extensions":{"persistedQuery":{"version":1,"sha256Hash":"d7fbdb4e9780dcdc0cc1618ec783309471cd05a59584fc3c56ea1c52bb632d41"}}}
        data = {
            "operationName": "FollowButton_FollowUser",
            "variables": {
                "input": {
                    "disableNotifications": False,
                    "targetID": target_id}},
            "extensions": {
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "3efee1acda90efdff9fef6e6b4a29213be3ee490781c5b54469717b6131ffdfe"}
            }
        }

        res = requests.post(
            'https://gql.twitch.tv/gql',
            headers=headers,
            data=json.dumps(data)).json()
        print(res)
        return res

    except Exception as e:
        print(e)


def get_user(user, tokens):
    try:
        data = [
            {
                "operationName": "ChannelAvatar",
                "variables": {
                    "channelLogin": user
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "84ed918aaa9aaf930e58ac81733f552abeef8ac26c0117746865428a7e5c8ab0"
                    }
                }
            }
        ]
        response = requests.post(
            'https://gql.twitch.tv/gql',
            headers={
                'Authorization': 'Bearer ' + tokens,
                'Client-ID': 'kimne78kx3ncx6brgo4mv6wki5h1ko'
            },
            data=json.dumps(data)
        )
        print(response.json())

        target_id = response.json()[0]['data']['user']['id']
        followers_count = response.json()[0]['data']['user']['followers']['totalCount']
    except Exception as e:
        print(str(e))
        exit()
    else:
        return target_id, followers_count


if __name__ == '__main__':
    user = input('Username:')
    tokens = open(r'all_tokens.txt', 'r').read().splitlines()
    target_id, current_followers = get_user(user, tokens[0])
    amount = 0

    while True:
        amount = int(input("Сколько крутить подписчиков:"))
        if amount > len(tokens):
            print(
                "Недостаточное количество токенов для накрутки " + str(amount) + " подписчиков.\nИмеется только " + str(
                    len(tokens)) + "токенов.")
        else:
            break

    pool = ThreadPool(processes=10)
    results = pool.map(follow_user, [i for i in tokens[:amount]])
    target_id, followers_count = get_user(user, tokens[0])
    print(user)
    print(f'Res: {current_followers}>{followers_count}')
    input()

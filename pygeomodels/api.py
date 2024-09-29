import requests


def restapi_get(host, method, access_token):
    # For example,
    #   host = "http://modelmanager:7504"
    #   method = "mbms/v1/model-manager/general-models/catalog"
    url = f"{host}/{method}"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers)
    # print(url)
    if resp.status_code == 200:
        try:
            jsondata = resp.json()
            return jsondata
        except:
            print('Cannot get JSON data from %s' % url)
    else:
        print('Get API (%s) failed!' % url)
        return None


def restapi_post(host, method, body, access_token):
    url = f"{host}/{method}"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.post(url, json=body, headers=headers)
    if resp.status_code == 200:
        try:
            jsondata = resp.json()
            return jsondata
        except:
            print('Cannot POST API %s' % url)
    else:
        print('POST API (%s) failed!' % url)
        return None


if __name__ == "__main__":
    pass

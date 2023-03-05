"""
REST api hívások.
A mudulban található apihívás típusok: post, get (még bővíteni kell minimum egy puttal)
Minden hívás tartalmaz egy performancia tesztet is, amit a hívás után meghívva visszadja, hogy mennyi időt igényelt a hívíás elküldésétől számítva a response beérkezése
"""
import copy
from functools import wraps

import requests

from lighttest_basic.http_headers import HttpHeaders
from time import perf_counter
from lighttest_supplies.encoding import binary_json_to_json
from lighttest_supplies.general_datas import TestType as tt
import json
import aiohttp
from lighttest_basic.datacollections import BackendResultDatas


def collect_call_request_data(request_function):
    @wraps(request_function)
    def rest_api_call(*args, **kwargs):
        call_object: Calls = args[0]
        start_time = perf_counter()
        request_function(*args, **kwargs)
        call_object.response
        end_time = perf_counter()
        call_object.response_time: float = round(end_time - start_time, 2)

        call_object.request = binary_json_to_json(call_object.response.request.body)

        try:
            call_object.response_json = call_object.response.json()
        except json.decoder.JSONDecodeError:
            call_object.response_json: dict = {"error": "it is not json format or there is no response object"}
        call_object.status_code = call_object.response.status_code
        call_object.response_headers = call_object.response.headers
        call_object.url = call_object.response.url
        return call_object

    return rest_api_call


async def collect_async_data(resp: object, request: dict):
    result: BackendResultDatas = copy.deepcopy(BackendResultDatas())
    result.response_headers = resp.headers
    result.status_code = resp.status
    result.request = request
    result.url = str(resp.url)
    try:
        result.response_json = await resp.json()
    except aiohttp.client_exceptions.ContentTypeError:
        result.response_json = {}
    result.response_time = 0
    return result


class Calls(HttpHeaders):

    def __init__(self):
        super().__init__()
        self.response: object = None
        self.response_time: float = 0.0
        self.request: object = None
        self.response_json: dict = {}
        self.status_code: int = 0
        self.response_headers: dict = {}
        self.url: str = ""

    @collect_call_request_data
    def post_call(self, uri_path: str, payload: dict, param: str = ""):
        self.response = requests.post(url=f'{self.get_base_url()}{uri_path}{param}', headers=self.get_headers(),
                                      json=payload)

    @collect_call_request_data
    def get_call(self, uri_path: str, payload: dict = {}, param=""):
        self.response = requests.get(url=f'{self.get_base_url()}{uri_path}{param}', headers=self.get_headers(),
                                     json=payload)

    @collect_call_request_data
    def put_call(self, uri_path: str, payload: dict, param: str = ""):
        self.response = requests.put(url=f'{self.get_base_url()}{uri_path}{param}', headers=self.get_headers(),
                                     json=payload)

    @collect_call_request_data
    def delete_call(self, uri_path: str, payload: dict, param: str = ""):
        self.response = requests.delete(
            url=f'{self.get_base_url()}{uri_path}{param}', headers=self.get_headers(), json=payload)


async def post_req_task(uri_path, request: dict, session):
    async with session.post(url=f'{Calls.global_base_url}{uri_path}', json=request) as resp:
        return await collect_async_data(resp=resp, request=request)


async def get_req_task(uri_path, session, request: dict, param=""):
    async with session.get(url=f'{Calls.global_base_url}{uri_path}{param}') as resp:
        return await collect_async_data(resp=resp, request=request)


async def put_req_task(uri_path, session, request: dict, param=""):
    async with session.put(url=f'{Calls.global_base_url}{uri_path}{param}', json=request) as resp:
        return await collect_async_data(resp=resp, request=request)

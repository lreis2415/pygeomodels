# -*- coding: utf-8 -*-
# Exercise 1: Using pygeomodels to submit model task
import os, sys

from pygeomodels.modelBank import modelBank
from pygeomodels.api import get_task_status

def main():
    """
    """
    model_bank = modelBank()
    caller = model_bank.models_caller
    inputs = {"z": "/onesis/kt4/dem/dem_meixi.tif"}
    params = {}
    outputs = {"fel": "/onesis/kt4/dem/dem_meixi_fel.tif"}

    result = caller.pitRemove(inputs, params, outputs)
    task_id = ''
    if result['success']:
        print('Task submitted succeed, task ID: %s' % result['data']['task_id'])
        task_id = result['data']['task_id']
    else:
        print('Task submitted failed: %s' % result['message'])

    if task_id:
        task_resp = get_task_status(task_id)
        if task_resp['success']:
            print('Task status: %s' % task_resp['status'])
            print('Task log: %s' % task_resp['log'])


if __name__ == "__main__":
    main()

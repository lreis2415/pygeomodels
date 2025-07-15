# -*- coding: utf-8 -*-
# Exercise 1: Using pygeomodels to submit model task
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import time

from pygeomodels.config import parse_config
from pygeomodels.modelBank import modelBank
from pygeomodels.modelTask import modelTask


def main():
    """
    """
    cfg = parse_config()
    model_bank = modelBank(cfg)

    # It may take some time to fetch all model metadata from server
    # and generate the callable functions.
    print('Initializing model caller, please wait...')
    caller = model_bank.models_caller
    print('Model caller initialized.')

    # TODO: Users should change the following paths to their own.
    inputs = {"z": "/onesis/kt4/dem/dem_meixi.tif"}
    params = {}
    outputs = {"fel": "/onesis/kt4/dem/dem_meixi_fel.tif"}

    project_id = caller.pitRemove(inputs, params, outputs)

    if project_id:
        print(f'Task submitted succeed, project ID: {project_id}')

        model_task = modelTask(cfg, project_id)

        # Wait for a while so that the task is initialized.
        print("Waiting for 5 seconds before checking status...")
        time.sleep(5)

        # You can get progress, log, data, etc.
        progress = model_task.progress()
        if progress:
            print(f'Task progress: {progress}')

        log = model_task.log()
        if log:
            print(f'Task log: {log}')
    else:
        print('Task submitted failed.')


if __name__ == "__main__":
    main()

"""Executa notebooks de cima para baixo no modo sintético e guarda cópias fora do Git."""
from pathlib import Path
import json
import os
import sys
import time
import nbformat
from nbclient import NotebookClient


def main():
    root=Path(__file__).resolve().parents[1]
    output=root/'experiments'/'validation'/'executed_notebooks'
    output.mkdir(parents=True,exist_ok=True)
    os.environ['TCC_ROOT']=str(root)
    os.environ['TCC_RUN_MODE']='synthetic'
    os.environ['TCC_RUN_TRAINING_SMOKE']='0'  # o smoke tem comando/teste próprio
    os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
    os.environ['IPYTHONDIR']=str(root/'.cache'/'ipython')
    os.environ['JUPYTER_RUNTIME_DIR']=str(root/'.cache'/'jupyter_runtime')
    report=[]
    from jupyter_client.kernelspec import KernelSpecManager
    kernels=root/'.cache'/'kernels'
    spec=kernels/'python3'; spec.mkdir(parents=True,exist_ok=True)
    (spec/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
                                             'display_name':'TCC Python','language':'python'}),encoding='utf-8')
    manager=KernelSpecManager(kernel_dirs=[str(kernels)])
    from jupyter_client import KernelManager
    for path in sorted((root/'notebooks').glob('[0-9][0-9]_*.ipynb')):
        start=time.perf_counter()
        nb=nbformat.read(path,as_version=4)
        nbformat.validate(nb)
        kernel=KernelManager(kernel_name='python3',kernel_spec_manager=manager)
        client=NotebookClient(nb,timeout=180,resources={'metadata':{'path':str(root)}},km=kernel)
        client.execute()
        nbformat.write(nb,output/path.name)
        report.append({'notebook':path.name,'status':'passed','mode':'synthetic',
                       'training_smoke_in_notebook':False,'seconds':time.perf_counter()-start})
        print(path.name,'passed',flush=True)
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__': main()

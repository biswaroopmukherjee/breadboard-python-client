import json
import pandas as pd
import datetime
import dateutil
import re
from tqdm.auto import tqdm
import logging

from warnings import warn



class RunMixin:
    """ Useful functions for Run queries through the breadboard Client
    Plugs into breadboard/client.py
    """


    def get_runs(self, datetime_range=None, page='', **kwargs):
        """
        Returns all the API data corresponding to a set of runs as JSON

        Query modes:
        0) Nothing: returns a list of runs, paginated
        1) datetime range: get all runs between two times

        Inputs:
        - datetime_range: a [start, end] array of python datetimes
        
        Outputs:
        - a json object containing the entire response from the API

        """

        if datetime_range:
            datetime_range = [clean_run_time(run_time) for run_time in datetime_range]
        else:
            datetime_range = [None, None]
    
        payload_dirty = {
            'lab': self.lab_name,
            'start_datetime': datetime_range[0],
            'end_datetime': datetime_range[1],
            **kwargs
        }

        payload_clean = {k: v for k, v in payload_dirty.items() if not (
                        v==None or
                        (isinstance(v, tuple) and (None in v))
                )}
        logging.debug(payload_clean)

        response = self._send_message('get', '/runs/'+page, params=payload_clean)
 
        if not response.json().get('results'):
            raise RuntimeError(response.json().get('detail'))
        return response




    def get_runs_df(self, paramsin="list_bound_only", xvar='unixtime', extended=False, tqdm_disable=False, **kwargs):
        """ Return a pandas dataframe for run data
        Inputs:
        - paramsin:
            > ['param1','param2',...] : a list of params
            > '*' for all params
            > 'list_bound_only' for listbound params only
        - xvar: a variable to use as df.x
        - extended: a boolean to show all the keys from the run, like the url and id
        - datetime_range: a [start, end] array of python datetimes
 

        Outputs:
        - df: the dataframe with params

        
        """
        

        
        # Get the first page
        response = self.get_runs(**kwargs)
        jsonresponse = response.json()
        runs = jsonresponse.get('results')


        # Prepare df
        df = pd.DataFrame(columns = ['runtime'])
        try:
            df['runtime'] = [run['runtime'] for run in runs]
        except:
            raise RuntimeError('Couldnt extract runtimes')
        df['x'] = 0

        # Prepare params:
        if extended:
            paramsall = set(runs[0].keys())
        else:
            paramsall = set()
        if paramsin=='*':
            #  Get all params
            for jr in runs:
                try:    params = set(jr['parameters'].keys())
                except: params = set()
                paramsall = paramsall.union(params)
        elif paramsin=='list_bound_only':
            # Get listbound params
            for jr in runs:
                try:    params = set(jr['parameters']['ListBoundVariables'])
                except: params = set()
                paramsall = paramsall.union(params)
        else:# use set of params provided
            if isinstance(paramsin, str):
                paramsin = [paramsin]
            paramsall = paramsall.union(set(paramsin))

        removeparams = set([
                    'ListBoundVariables',
                    ])
        addparams = set([
                    'unixtime'
                    ])

        paramsall = (paramsall - removeparams).union(addparams)



        # Populate dataframe
        for i, _ in df.iterrows():

            try: # to get the runtime
                runtime = runs[i]['runtime']
            except:
                runtime = '1970'
                warn('no run found for some runs')

            for param in paramsall:

                if param=='runtime':
                    df.at[i, param] = runtime
                elif param=='unixtime':
                    df.at[i, param] = int(dateutil.parser.parse(runtime).timestamp())
                else:
                    # try to get run params
                    try: df.at[i,param] = runs[i]['parameters'][param]
                    except:
                        # try to get the bare run parameters
                        try:    df.at[i,param] = runs[i][param]
                        except: df.at[i,param] = float('nan') # nan the rest


        # Get the xvar
        try:        df['x'] = df[xvar]
        except:     warn('Invalid xvar!')

        df = df.sort_values(by='runtime', ascending=True).reset_index(drop=True)

        return df


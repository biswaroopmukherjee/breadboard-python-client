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
            datetime_range = [clean_run_time(run_time)
                              for run_time in datetime_range]
        else:
            datetime_range = [None, None]

        payload_dirty = {
            'lab': self.lab_name,
            'start_datetime': datetime_range[0],
            'end_datetime': datetime_range[1],
            **kwargs
        }

        payload_clean = {k: v for k, v in payload_dirty.items() if not (
            v == None or
            (isinstance(v, tuple) and (None in v))
        )}
        logging.debug(payload_clean)

        response = self._send_message(
            'get', '/runs/' + page, params=payload_clean)

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
        df = pd.DataFrame(columns=['runtime'])
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
        if paramsin == '*':
            #  Get all params
            for jr in runs:
                try:
                    params = set(jr['parameters'].keys())
                except:
                    params = set()
                paramsall = paramsall.union(params)
        elif paramsin == 'list_bound_only':
            # Get listbound params
            for jr in runs:
                try:
                    params = set(jr['parameters']['ListBoundVariables'])
                except:
                    params = set()
                paramsall = paramsall.union(params)
        else:  # use set of params provided
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

            try:  # to get the runtime
                runtime = runs[i]['runtime']
            except:
                runtime = '1970'
                warn('no run found for some runs')

            for param in paramsall:

                if param == 'runtime':
                    df.at[i, param] = runtime
                elif param == 'unixtime':
                    df.at[i, param] = int(
                        dateutil.parser.parse(runtime).timestamp())
                else:
                    # try to get run params
                    try:
                        df.at[i, param] = runs[i]['parameters'][param]
                    except:
                        # try to get the bare run parameters
                        try:
                            df.at[i, param] = runs[i][param]
                        except:
                            df.at[i, param] = float('nan')  # nan the rest

        # Get the xvar
        try:
            df['x'] = df[xvar]
        except:
            warn('Invalid xvar!')

        df = df.sort_values(
            by='runtime', ascending=True).reset_index(drop=True)

        return df

    def add_measurement_name_to_run(self, run_id, measurement_name):
        run_dict = self._send_message(
            'get', '/runs/' + str(run_id) + '/').json()
        if 'measurement_name' in run_dict['parameters']:
            raise ValueError(
                'This run_id is already associated with a measurement.')
        run_dict['parameters'].update({'measurement_name': measurement_name})
        payload = json.dumps(run_dict)
        response = self._send_message(
            'put', '/runs/' + str(run_id) + '/', data=payload)
        return response

    def append_images_to_run(self, run_id, image_filenames, measurement_name=None, printing=True):
        if isinstance(image_filenames, str):
            image_filenames = [image_filenames]
        run_dict = self._send_message(
            'get', '/runs/' + str(run_id) + '/').json()
        if 'image_filenames' in run_dict['parameters']:
            image_filenames = list(set().union(
                run_dict['parameters']['image_filenames'], image_filenames))
            warn('Images were already associated with this run_id.')
        run_dict['parameters'].update({'image_filenames': image_filenames})
        payload = json.dumps(run_dict)
        response = self._send_message(
            'put', '/runs/' + str(run_id) + '/', data=payload)
        if printing:
            print('run_id ' + str(run_id) + ' associated with ' +
                  str(image_filenames) + '\n')
            for var in run_dict['parameters']['ListBoundVariables']:
                print(var + ': ')
                print(run_dict['parameters'][var])
        if measurement_name is not None:
            self.add_measurement_name_to_run(run_id, measurement_name)
        return response

    def append_analysis_to_run(self, run_id, analysis_dict, printing=True):
        run_dict = self._send_message(
            'get', '/runs/' + str(run_id) + '/').json()
        if 'analyzed_variables' in run_dict['parameters']:
            analyzed_variables = list(set().union(
                run_dict['parameters']['analyzed_variables'], [var_name for var_name in analysis_dict]))
        run_dict['parameters'].update(analysis_dict)
        payload = json.dumps(run_dict)
        response = self._send_message(
            'put', '/runs/' + str(run_id) + '/', data=payload)
        if printing:
            print('run_id ' + str(run_id) + ' analyzed: ' +
                  str(analysis_dict) + '\n')
            for var in run_dict['parameters']['ListBoundVariables']:
                print(var + ': ')
                print(run_dict['parameters'][var])
        return response

    def add_measurement_name_to_run(self, run_id, measurement_name):
        run_dict = self._send_message(
            'get', '/runs/' + str(run_id) + '/').json()
        if 'measurement_name' in run_dict['parameters']:
            raise ValueError(
                'This run_id is already associated with a measurement.')
        run_dict['parameters'].update({'measurement_name': measurement_name})
        payload = json.dumps(run_dict)
        response = self._send_message(
            'put', '/runs/' + str(run_id) + '/', data=payload)
        return response

    def get_runs_df_from_ids(self, run_ids, optional_column_names=[]):
        if not isinstance(run_ids, list):
            run_ids = [run_ids]
        idx = 0

        for run_id in run_ids:
            display_run_dict = {}
            if isinstance(run_id, int):
                run_id = str(run_id)
            resp = self._send_message(
                'get', '/runs/{run_id}/'.format(run_id=run_id)).json()
            display_run_dict['run_id'] = int(run_id)
            run_dict = resp['parameters']
            if 'badshot' not in run_dict:
                display_run_dict['badshot'] = False
            else:
                display_run_dict['badshot'] = run_dict['badshot']
            display_run_dict.update({'notes': resp['notes']})
            for key in run_dict:
                if 'manual_' in key:
                    display_run_dict.update({key: run_dict[key]})
            for column in optional_column_names:
                if column in run_dict:
                    display_run_dict.update({column: run_dict[column]})
            if 'analyzed_variables' in run_dict:
                display_run_dict.update(
                    {key: run_dict[key] for key in run_dict['analyzed_variables']})
            display_run_dict.update(
                {key: run_dict[key] for key in run_dict['ListBoundVariables']})

            if idx == 0:
                df = pd.DataFrame(display_run_dict, index=[0])
            else:
                df = df.append(display_run_dict, ignore_index=True)
            idx += 1
        return df

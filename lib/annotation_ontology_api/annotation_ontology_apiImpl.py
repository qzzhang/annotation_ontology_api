# -*- coding: utf-8 -*-
#BEGIN_HEADER
import os
import requests
from pprint import pformat
from annotation_ontology_api.annotation_ontology_api import AnnotationOntologyAPI
from Workspace.WorkspaceClient import Workspace as workspaceService
from DataFileUtil.DataFileUtilClient import DataFileUtil
# silence whining
import requests
requests.packages.urllib3.disable_warnings()
#END_HEADER


class annotation_ontology_api:
    '''
    Module Name:
    annotation_ontology_api

    Module Description:
    A KBase module: annotation_ontology_api
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.config = config
        self.ws_client = None
        self.dfu_client = None
        if 'SDK_CALLBACK_URL' in os.environ:
            self.config['SDK_CALLBACK_URL'] = os.environ['SDK_CALLBACK_URL']
            self.dfu_client = DataFileUtil(self.config['SDK_CALLBACK_URL'])
            self.config['KB_AUTH_TOKEN'] = os.environ['KB_AUTH_TOKEN']
            self.ws_client = workspaceService(config["workspace-url"])
        #END_CONSTRUCTOR
        pass


    def get_annotation_ontology_events(self, ctx, params):
        """
        Retrieves annotation ontology events in a standardized form cleaning up inconsistencies in underlying data
        :param params: instance of type "GetAnnotationOntologyEventsParams"
           -> structure: parameter "input_ref" of String, parameter
           "input_workspace" of String, parameter "query_events" of list of
           String, parameter "query_genes" of list of String
        :returns: instance of type "GetAnnotationOntologyEventsOutput" ->
           structure: parameter "events" of list of type
           "AnnotationOntologyEvent" -> structure: parameter "event_id" of
           String, parameter "ontology_id" of String, parameter "method" of
           String, parameter "method_version" of String, parameter
           "timestamp" of String, parameter "ontology_terms" of mapping from
           String to list of type "AnnotationOntologyTerm" (Insert your
           typespec information here.) -> structure: parameter "term" of
           String, parameter "modelseed_id" of String, parameter "evidence"
           of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN get_annotation_ontology_events
        self.config['ctx'] = ctx
        #print(("Input parameters: " + pformat(params)))
        anno_api = None
        if self.ws_client == None:
            if "workspace-url" in params:
                anno_api = AnnotationOntologyAPI(self.config,workspaceService(params['workspace-url'], token=ctx['token']),self.dfu_client)
            else:
                anno_api = AnnotationOntologyAPI(self.config,workspaceService(self.config['workspace-url'], token=ctx['token']),self.dfu_client)
        else:
            anno_api = AnnotationOntologyAPI(self.config,self.ws_client,self.dfu_client)
        output = anno_api.get_annotation_ontology_events(params)
        #END get_annotation_ontology_events

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method get_annotation_ontology_events return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]

    def add_annotation_ontology_events(self, ctx, params):
        """
        Adds a new annotation ontology event to a genome or AMA
        :param params: instance of type "AddAnnotationOntologyEventsParams"
           -> structure: parameter "input_ref" of String, parameter
           "input_workspace" of String, parameter "output_name" of String,
           parameter "output_workspace" of String, parameter "events" of list
           of type "AnnotationOntologyEvent" -> structure: parameter
           "event_id" of String, parameter "ontology_id" of String, parameter
           "method" of String, parameter "method_version" of String,
           parameter "timestamp" of String, parameter "ontology_terms" of
           mapping from String to list of type "AnnotationOntologyTerm"
           (Insert your typespec information here.) -> structure: parameter
           "term" of String, parameter "modelseed_id" of String, parameter
           "evidence" of String
        :returns: instance of type "AddAnnotationOntologyEventsOutput" ->
           structure: parameter "output_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN add_annotation_ontology_events
        self.config['ctx'] = ctx
        #print(("Input parameters: " + pformat(params)))
        anno_api = None
        if self.ws_client == None:
            if "workspace-url" in params:
                anno_api = AnnotationOntologyAPI(self.config,workspaceService(params['workspace-url'], token=ctx['token']),self.dfu_client)
            else:
                anno_api = AnnotationOntologyAPI(self.config,workspaceService(self.config['workspace-url'], token=ctx['token']),self.dfu_client)
        else:
            anno_api = AnnotationOntologyAPI(self.config,self.ws_client,self.dfu_client)
        output = anno_api.add_annotation_ontology_events(params)
        #END add_annotation_ontology_events

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method add_annotation_ontology_events return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]

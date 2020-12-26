import json
import os
import re

# silence whining
import requests
requests.packages.urllib3.disable_warnings()

source_hash = {
    "MetaCyc" : "META",
    "KEGG" : "RO",
    "BiGG" : "BIGG",
    "rhea" : "RHEA"
}

ontology_translation = {
    "KEGGKO" : "KO",
    "KEGGRO" : "RO",
    "METACYC" : "META",
    "SEED" : "SSO",
    "TCDB" : "TC",
    "MODELSEED" : "MSRXN"
}

ontology_hash = {
    "KO" : 1,
    "EC" : 1,
    "SSO" : 1,
    "RO" : 1,
    "META" : 1,
    "MSRXN" : 1,
    "MSCPD" : 1,
    "MSCPX" : 1,
    "BIGG" : 1,
    "BIGGCPD" : 1,
    "GO" : 1,
    "TC" : 1,
    "RHEA" : 1
};

class AnnotationOntologyAPI:
    def __init__(self,config,ws_client = None, dfu_client = None):
        self.ws_client = ws_client
        self.dfu_client = dfu_client
        self.alias_hash = {}
        self.term_names = {}
        self.config = config
    
    def process_workspace_identifiers(self,id_or_ref, workspace=None):
        """
        IDs should always be processed through this function so we can interchangeably use
        refs, IDs, and names for workspaces and objects
        """
        objspec = {}
        if workspace is None or len(id_or_ref.split("/")) > 1:
            objspec["ref"] = id_or_ref
        else:
            if isinstance(workspace, int):
                objspec['wsid'] = workspace
            else:
                objspec['workspace'] = workspace
            if isinstance(id_or_ref, int):
                objspec['objid'] = id_or_ref
            else:
                objspec['name'] = id_or_ref
                
        #print("Object spec:")
        #for key in objspec:
        #    print(key+"\t"+objspec[key])
        return objspec
    
    def get_alias_hash(self,namespace):
        if "MSRXN" not in self.alias_hash:
            filename = self.config["data_directory"]+"/msrxn_hash.json"
            with open(filename) as json_file:
                self.alias_hash["MSRXN"] = json.load(json_file)
        if namespace not in self.alias_hash:
            self.alias_hash[namespace] = {}
            if namespace == "EC":
                filename = self.config["data_directory"]+"/EC_translation.tsv"
                data = ""
                with open(filename, 'r') as file:
                    data = file.read()
                lines = data.split("\n")
                lines.pop(0)
                for line in lines:
                    items = line.split("\t")
                    if len(items) >= 2:
                        modelseed = "MSRXN:"+items[0]
                        if modelseed in self.alias_hash["MSRXN"]:
                            modelseed = self.alias_hash["MSRXN"][modelseed][0]
                        if items[1] not in self.alias_hash["EC"]:
                            self.alias_hash["EC"]["EC:"+items[1]] = []
                        self.alias_hash["EC"]["EC:"+items[1]].append(modelseed)
            elif namespace == "META" or namespace == "RO" or namespace == "BIGG" or namespace == "RHEA":
                filename = self.config["data_directory"]+"/ModelSEED_Reaction_Aliases.txt"
                data = ""
                with open(filename, 'r') as file:
                    data = file.read()
                lines = data.split("\n")
                for line in lines:
                    items = line.split("\t")
                    if len(items) >= 3:
                        modelseed = "MSRXN:"+items[0]
                        if modelseed in self.alias_hash["MSRXN"]:
                            modelseed = self.alias_hash["MSRXN"][modelseed][0]
                        source = None
                        if items[2] in source_hash:
                            source = source_hash[items[2]]
                        if source != None:
                            if source not in self.alias_hash:
                                self.alias_hash[source] = {}
                            if items[1] not in self.alias_hash[source]:
                                self.alias_hash[source][source+":"+items[1]] = []
                            self.alias_hash[source][source+":"+items[1]].append(modelseed)
            elif namespace == "KO":
                filename = self.config["data_directory"]+"/kegg_95_0_ko_seed.tsv"
                data = ""
                with open(filename, 'r') as file:
                    data = file.read()
                lines = data.split("\n")
                lines.pop(0)
                for line in lines:
                    items = line.split("\t")
                    if len(items) >= 2:
                        if items[0] not in self.alias_hash["KO"]:
                            self.alias_hash["KO"]["KO:"+items[0]] = []
                        modelseed_ids = items[1].split(";")
                        id_hash = {}
                        for modelseed in modelseed_ids:
                            modelseed = "MSRXN:"+modelseed
                            if modelseed in self.alias_hash["MSRXN"]:
                                modelseed = self.alias_hash["MSRXN"][modelseed][0]
                            if modelseed not in id_hash:
                                self.alias_hash["KO"]["KO:"+items[0]].append(modelseed)
                            id_hash[modelseed] = 1
            elif namespace == "SSO":
                sso_template = dict()
                filename = self.config["data_directory"]+"/SSO_reactions.json"
                with open(filename) as json_file:
                    sso_template = json.load(json_file)
                for sso in sso_template:
                    id_hash = {}
                    for modelseed in sso_template[sso]:
                        modelseed = "MSRXN:"+modelseed
                        if modelseed in self.alias_hash["MSRXN"]:
                            modelseed = self.alias_hash["MSRXN"][modelseed][0]
                            if modelseed not in id_hash:
                                if sso not in self.alias_hash["SSO"]:
                                    self.alias_hash["SSO"][sso] = []
                                self.alias_hash["SSO"][sso].append(modelseed)
                            id_hash[modelseed] = 1             
            elif namespace == "GO":
                go_translation = dict()
                filename = self.config["data_directory"]+"/GO_ontology_translation.json"
                with open(filename) as json_file:
                    go_translation = json.load(json_file)
                for term in go_translation["translation"]:
                    adjusted_term = "GO:"+term
                    if "equiv_terms" in go_translation["translation"][term]:
                        id_hash = {}
                        for rxn_data in go_translation["translation"][term]["equiv_terms"]:
                            modelseed = rxn_data["equiv_term"]
                            if modelseed in self.alias_hash["MSRXN"]:
                                modelseed = self.alias_hash["MSRXN"][modelseed][0]
                            if adjusted_term not in self.alias_hash["KO"]:
                                self.alias_hash["GO"][adjusted_term] = []
                            if modelseed not in id_hash:
                                self.alias_hash["GO"][adjusted_term].append(modelseed)
                            id_hash[modelseed] = 1                   
        return self.alias_hash[namespace]
                
    def translate_term_to_modelseed(self,term):
        namespace = term.split(":").pop(0)
        if namespace == "MSRXN":
            if term not in self.get_alias_hash(namespace):
                return [term]
            else:
                return self.get_alias_hash(namespace)[term]
        elif term not in self.get_alias_hash(namespace):
            return []
        else:
            return self.get_alias_hash(namespace)[term]
        
    def get_annotation_ontology_events(self,params):
        #Building query hash
        event_query = None
        if "query_events" in params and not params["query_events"] == None:
            for event in params["query_events"]:
                event_query[event] = 1
        gene_query = None
        if "query_genes" in params and not params["query_genes"] == None:
            for gene in params["query_genes"]:
                gene_query[gene] = 1
        #Pull the object from the workspace is necessary
        if "object" not in params:
            res = self.ws_client.get_objects2({"objects": [self.process_workspace_identifiers(params["input_ref"], params["input_workspace"])]})
            params["object"] = res["data"][0]["data"]
            params["type"] = res["data"][0]["info"][2]
        #Get the feature data
        features = []
        types = {}
        if "features" in params["object"]:
            features.extend(params["object"]["features"])
            for ftr in params["object"]["features"]:
                types[ftr["id"]] = "gene"
        if "cdss" in params["object"]:
            features.extend(params["object"]["cdss"])
            for ftr in params["object"]["cdss"]:
                types[ftr["id"]] = "cds"
        if "mrnas" in params["object"]:
            features.extend(params["object"]["mrnas"])
            for ftr in params["object"]["mrnas"]:
                types[ftr["id"]] = "mrna"
        if "non_coding_features" in params["object"]:
            features.extend(params["object"]["non_coding_features"])
            for ftr in params["object"]["non_coding_features"]:
                types[ftr["id"]] = "noncoding"
        elif "features_handle_ref" in params["object"]:
            shock_output = self.dfu_client.shock_to_file({
                "handle_id" : params["object"]["features_handle_ref"],
                "file_path" : self.scratch_path
            })
            os.system("gunzip --force ".shock_output["file_path"])
            shock_output["file_path"] = shock_output["file_path"][0:-3]
            with open(shock_output["file_path"]) as json_file:
                features = json.load(json_file)
            for ftr in features:
                types[ftr["id"]] = "gene"
        output = {"events" : [],"feature_types" : {}}
        if "ontology_events" in params["object"]:
            events_array = []
            for event in params["object"]["ontology_events"]:
                id = None
                if "description" in event:
                    id = event["description"]
                else: 
                    id = event["method"]+":"+event["method_version"]+":"+event["id"]+":"+event["timestamp"]
                newevent = {
                    "event_id" : id,
                    "ontology_id" : event["id"],
                    "method" : event["method"],
                    "method_version" : event["method_version"],
                    "timestamp" : event["timestamp"],
                    "ontology_terms" : {}
                }
                newevent["ontology_id"] = newevent["ontology_id"].upper()
                if newevent["ontology_id"] not in ontology_hash and newevent["ontology_id"] in ontology_translation:
                    newevent["ontology_id"] = ontology_translation[newevent["ontology_id"]]
                events_array.append(newevent)
                if event_query == None or id in event_query:
                    output["events"].append(newevent)
            for feature in features:
                if gene_query == None or feature["id"] in gene_query:
                    if "ontology_terms" in feature:
                        for tag in feature["ontology_terms"]:
                            original_tag = tag
                            tag = tag.upper()
                            if tag not in ontology_hash and tag in ontology_translation:
                                tag = ontology_translation[tag]
                            if tag in ontology_hash:
                                for term in feature["ontology_terms"][original_tag]:
                                    original_term = term
                                    array = term.split(":")
                                    if len(array) == 1:
                                        term = tag+":"+array[0]
                                    else:
                                        if array[0] == original_tag or array[0] == original_tag.upper():
                                            array[0] = tag
                                            term = ":".join(array)
                                        else:
                                            term = ":".join(array)
                                            term = tag+":"+term
                                    modelseed_ids = self.translate_term_to_modelseed(term)
                                    for event_index in feature["ontology_terms"][original_tag][original_term]:
                                        if feature["id"] not in events_array[event_index]["ontology_terms"]:
                                            output["feature_types"][feature["id"]] = types[feature["id"]]
                                            events_array[event_index]["ontology_terms"][feature["id"]] = []
                                        termdata = {"term" : term}
                                        if len(modelseed_ids) > 0:
                                            termdata["modelseed_ids"] = modelseed_ids
                                        if "ontology_evidence" in feature:
                                            if original_term in feature["ontology_evidence"]:
                                                if event_index in feature["ontology_evidence"][original_term]:
                                                    termdata["evidence"] = feature["ontology_evidence"][original_term][event_index]
                                        events_array[event_index]["ontology_terms"][feature["id"]].append(termdata)
        return output
    
    def add_annotation_ontology_events(self,params):
        #Pull the object from the workspace is necessary
        if "object" not in params or params["object"] == None:
            res = self.ws_client.get_objects2({"objects": [self.process_workspace_identifiers(params["input_ref"], params["input_workspace"])]})
            params["object"] = res["data"][0]["data"]
            params["type"] = res["data"][0]["info"][2]
        output = {
            "ftrs_not_found" : [],"ftrs_found" : 0
        }
        #Pulling existing ontology so we can standardize and check for matches
        ontologies_present = {}
        events = self.get_annotation_ontology_events(params)["events"]
        if "clear_existing" in params and params["clear_existing"] == 1: 
            events = []
        #Scrolling through new events, stadardizing, and checking for matches
        for event in params["events"]:
            if "ontology_id" not in event:
                event["ontology_id"] = event["id"]
            event["ontology_id"] = event["ontology_id"].upper()
            if event["ontology_id"] in ontology_translation:
                event["ontology_id"] = ontology_translation[event["ontology_id"]]
            event["id"] = event["ontology_id"]
            #Creating description
            if "event_id" not in event:
                event["event_id"] = event["method"]+":"+event["ontology_id"]+":"+event["timestamp"]
            if "description" not in event:
                event["description"] = event["method"]+":"+event["method_version"]+":"+event["ontology_id"]+":"+event["timestamp"]
            elif event["description"].split(":").pop() != event["timestamp"]:
                event["description"] = event["description"]+":"+event["timestamp"]
            index = 0
            match = 0
            for existing_event in events:
                #If an existing event has a matching event ID, we overwrite it
                if existing_event["event_id"] == event["event_id"]:
                    match = 1
                    if "overwrite_matching" in params and params["overwrite_matching"] == 1:
                        events[index] = event
                index += 1
            if match == 0:
                events.append(event)
        #Filling feature hash with all feature types which should all have unique ids
        feature_hash = {}
        if "features" in params["object"]:
            for ftr in params["object"]["features"]:
                feature_hash[ftr["id"]] = ftr
        if "cdss" in params["object"]:
            for ftr in params["object"]["cdss"]:
                feature_hash[ftr["id"]] = ftr
        if "mrnas" in params["object"]:
            for ftr in params["object"]["mrnas"]:
                feature_hash[ftr["id"]] = ftr
        if "non_coding_features" in params["object"]:
            for ftr in params["object"]["non_coding_features"]:
                feature_hash[ftr["id"]] = ftr
        if "features_handle_ref" in params["object"]:
            if "feature_object" not in params:
                shock_output = self.dfu_client.shock_to_file({
                    "handle_id" : params["object"]["features_handle_ref"],
                    "file_path" : self.scratch_path
                })
                os.system("gunzip --force ".shock_output["file_path"])
                shock_output["file_path"] = shock_output["file_path"][0:-3]
                with open(shock_output["file_path"]) as json_file:
                    params["feature_object"] = json.load(json_file)
        if "feature_object" in params:
            for ftr in params["feature_object"]:
                feature_hash[ftr["id"]] = ftr
        #Adding events
        for event in events:
            new_event = {
                "description" : event["description"],
                "id" : event["ontology_id"],
                "event_id" : event["event_id"],
                "ontology_id" : event["ontology_id"],
                "method" : event["method"],
                "method_version" : event["method_version"],
                "timestamp" : event["timestamp"]
            }
            if "ontology_events" not in params["object"]:
                params["object"]["ontology_events"] = []
            event_index = len(params["object"]["ontology_events"])
            params["object"]["ontology_events"].append(new_event)
            for gene in event["ontology_terms"]:
                if gene in feature_hash:
                    output["ftrs_found"] += 1
                    feature = feature_hash[gene]
                    if "ontology_terms" not in feature:
                        feature["ontology_terms"] = {}
                    if new_event["id"] not in feature["ontology_terms"]:
                        feature["ontology_terms"][new_event["id"]] = {}
                    for term in event["ontology_terms"][gene]:
                        if term["term"].split(":")[0] != new_event["id"]:
                            term["term"] = new_event["id"]+":"+term["term"]
                        #If this is a SEED role, translate to an SSO
                        if new_event["id"] == "SSO" and re.search('^\d+$', term["term"]) == None:
                            term["term"] = self.translate_rast_function_to_sso(term["term"])
                        if term["term"] == None:
                            continue
                        if term["term"] not in feature["ontology_terms"][new_event["id"]]:
                            feature["ontology_terms"][new_event["id"]][term["term"]] = []
                        feature["ontology_terms"][new_event["id"]][term["term"]].append(event_index)
                        if new_event["id"] not in ontologies_present:
                            ontologies_present[new_event["id"]] = {}
                        ontologies_present[new_event["id"]][term["term"]] = self.get_term_name(new_event["id"],term["term"])
                        if "evidence" in term:
                            if "ontology_evidence" not in feature:
                                feature["ontology_evidence"] = {}
                            if term["term"] not in feature["ontology_evidence"]:
                                feature["ontology_evidence"][term["term"]] = {}
                            feature["ontology_evidence"][term["term"]][event_index] = term["evidence"]
                else:
                    output["ftrs_not_found"].append(gene)
        params["object"]["ontologies_present"] = ontologies_present
        #Saving object if requested but not if it's an AMA
        if params["save"] == 1:
            #Setting provenance
            provenance_params = {}
            for key in params:
                if not key == "object" and not key == "events" and not "feature_object":
                    provenance_params[key] = params[key]            
            provenance = [{
                'description': 'A function that adds ontology terms to a genome or metagenome',
                'input_ws_objects': [],
                'method': 'add_annotation_ontology_events',
                'method_params': [provenance_params],
                'service': 'annotation_ontology_api',
                'service_ver': 1,
            }]
            #If a metagenome, saving features
            if "feature_object" in params:
                json_file_path = self.config["scratch"]+params["object"]["name"]+"_features.json"
                with open(json_file_path, 'w') as fid:
                    json.dump(params["feature_object"], fid)
                json_to_shock = self.dfu_client.file_to_shock(
                    {'file_path': json_file_path, 'make_handle': 1, 'pack': 'gzip'}
                )
                # Resetting feature file handle o new value
                params["object"]['features_handle_ref'] = json_to_shock['handle']['hid']
                # Remove json file to avoid disk overload
                os.remove(json_file_path)
            # Removing genbank handle ref because this breaks saving
            params["object"].pop('genbank_handle_ref', None)
            # Saving genome/metagenome object to workspace
            ws_params = {
                'workspace': params["output_workspace"],
                'objects': [{
                    'data': params["object"],
                    'name': params["output_name"],
                    'type': params["type"],
                    'provenance': provenance
                }]
            }
            save_output = self.ws_client.save_objects(ws_params)
            output["output_ref"] = save_output[0][2]
        else:
            #Returning object if save not requested
            output["object"] = params["object"]
            output["type"] = params["type"]
            if "feature_object" in params:
                output["feature_object"] = params["feature_object"]
        return output
    
    def convert_role_to_searchrole(self,term):
        term = term.lower()
        term = re.sub("\s","",term)
        term = re.sub("[\d\-]+\.[\d\-]+\.[\d\-]+\.[\d\-]*","",term)
        term = re.sub("\#.*$","",term)
        term = re.sub("\(ec:*\)","",term)
        term = re.sub("[\(\)\[\],-]","",term)
        return term
    
    def translate_rast_function_to_sso(self,term):
        #Stripping out SSO prefix if it's present
        term = re.sub("^SSO:","",term)
        term = self.convert_role_to_searchrole(term)
        #Checking for SSO translation file
        if "SEED_ROLE" not in self.alias_hash:
            self.alias_hash["SEED_ROLE"] = {}
            sso_ontology = dict()
            with open(self.config["data_directory"]+"/SSO_dictionary.json") as json_file:
                sso_ontology = json.load(json_file)
            for term in sso_ontology["term_hash"]:
                name = self.convert_role_to_searchrole(sso_ontology["term_hash"][term]["name"])
                self.alias_hash["SEED_ROLE"][name] = term
            
        #Translating
        if term in self.alias_hash["SEED_ROLE"]:
            return self.alias_hash["SEED_ROLE"][term]
        else:
            return None
    
    def get_term_name(self,type,term):
        if type not in self.term_names:
            self.term_names[type] = {}
            if type == "SSO" or type == "EC" or type == "TC" or type == "META" or type == "RO" or type == "KO" or type == "GO":
                with open(self.config["data_directory"]+"/"+type+"_dictionary.json") as json_file:
                    ontology = json.load(json_file)
                    for term in ontology["term_hash"]:
                        self.term_names[type][term] = ontology["term_hash"][term]["name"]
        if term not in self.term_names[type]:
            return "Unknown"
        return self.term_names[type][term]
        
import {SelectFormField, SelectOption, VALID_UNLESS_REQUIRED_BUT_EMPTY, AND, IF} from '../Form';
import {AnalysisNetwork, Species} from '../KnowledgeNetwork';

// create a network name field for each species; they'll be enabled according to the current species selection, so only one will be visible at any given time
export function getInteractionNetworkOptions(species: Species[], networks: AnalysisNetwork[], labelNumber: string): SelectFormField[] {
    return species.map(s => {
        return new SelectFormField("network_name", null, labelNumber, "Select Interaction Network for analysis", "Interaction Network", true,
            networks.filter(n => n.species_number === s.species_number).map(n => new SelectOption(n.analysis_network_name, n.edge_type_name, n.selected_by_default)),
            false, VALID_UNLESS_REQUIRED_BUT_EMPTY, AND([IF('species', s.species_number), IF('use_network', true)]))
    });
};
/**
 * Real, verified enzyme sequences for demo and testing purposes.
 *
 * Sequences are fetched from UniProtKB (https://www.uniprot.org) using each
 * accession's canonical FASTA entry. These are wild-type, industrially
 * relevant enzymes covering the use cases Neolysis targets: detergents,
 * textiles/biofuel, food processing, and pulp/paper.
 *
 * Each preset intentionally omits an active-site residue definition, because
 * the real catalytic residue numbering depends on the specific structure file
 * used (PDB numbering can differ from the sequence's own numbering). Define
 * active sites after loading a matching structure on the Structure page,
 * rather than reusing residue numbers from a different enzyme.
 */

export interface EnzymePreset {
  id: string;
  label: string;
  enzymeName: string;
  organism: string;
  uniprotAccession: string;
  useCase: string;
  description: string;
  fastaHeader: string;
  sequence: string;
  suggestedConditions: {
    temperature_c: number;
    ph: number;
    salinity_m_m: number;
    solvent_exposure: string;
    use_case: string;
  };
}

export const enzymePresets: EnzymePreset[] = [
  {
    id: 'alkaline-protease',
    label: 'Alkaline protease (Subtilisin Carlsberg)',
    enzymeName: 'Subtilisin Carlsberg',
    organism: 'Bacillus licheniformis',
    uniprotAccession: 'P00780',
    useCase: 'Detergents (protein stain removal)',
    description: 'A serine protease widely used in laundry and dishwashing detergents to break down protein-based stains.',
    fastaHeader: '>sp|P00780|SUBC_BACLI Subtilisin Carlsberg OS=Bacillus licheniformis',
    sequence:
      'MMRKKSFWLGMLTAFMLVFTMAFSDSASAAQPAKNVEKDYIVGFKSGVKTASVKKDIIKE' +
      'SGGKVDKQFRIINAAKAKLDKEALKEVKNDPDVAYVEEDHVAHALAQTVPYGIPLIKADK' +
      'VQAQGFKGANVKVAVLDTGIQASHPDLNVVGGASFVAGEAYNTDGNGHGTHVAGTVAALD' +
      'NTTGVLGVAPSVSLYAVKVLNSSGSGSYSGIVSGIEWATTNGMDVINMSLGGASGSTAMK' +
      'QAVDNAYAKGVVVVAAAGNSGSSGNTNTIGYPAKYDSVIAVGAVDSNSNRASFSSVGAEL' +
      'EVMAPGAGVYSTYPTNTYATLNGTSMASPHVAGAAALILSKHPNLSASQVRNRLSSTATY' +
      'LGSSFYYGKGLINVEAAAQ',
    suggestedConditions: {
      temperature_c: 60,
      ph: 10,
      salinity_m_m: 250,
      solvent_exposure: 'moderate',
      use_case: 'detergent',
    },
  },
  {
    id: 'cellulase',
    label: 'Cellulase (Endoglucanase)',
    enzymeName: 'Endoglucanase (EglS)',
    organism: 'Bacillus subtilis',
    uniprotAccession: 'P10475',
    useCase: 'Textiles & biofuel (cellulose breakdown)',
    description: 'Breaks down cellulose fibers; used in textile bio-polishing/denim finishing and biomass/biofuel processing.',
    fastaHeader: '>sp|P10475|GUN2_BACSU Endoglucanase OS=Bacillus subtilis',
    sequence:
      'MKRSISIFITCLLITLLTMGGMIASPASAAGTKTPVAKNGQLSIKGTQLVNRDGKAVQLK' +
      'GISSHGLQWYGEYVNKDSLKWLRDDWGITVFRAAMYTADGGYIDNPSVKNKVKEAVEAAK' +
      'ELGIYVIIDWHILNDGNPNQNKEKAKEFFKEMSSLYGNTPNVIYEIANEPNGDVNWKRDI' +
      'KPYAEEVISVIRKNDPDNIIIVGTGTWSQDVNDAADDQLKDANVMYALHFYAGTHGQFLR' +
      'DKANYALSKGAPIFVTEWGTSDASGNGGVFLDQSREWLKYLDSKTISWVNWNLSDKQESS' +
      'SALKPGASKTGGWRLSDLSASGTFVRENILGTKDSTKDIPETPSKDKPTQENGISVQYRA' +
      'GDGSMNSNQIRPQLQIKNNGNTTVDLKDVTARYWYKAKNKGQNFDCDYAQIGCGNVTHKF' +
      'VTLHKPKQGADTYLELGFKNGTLAPGASTGNIQLRLHNDDWSNYAQSGDYSFFKSNTFKT' +
      'TKKITLYDQGKLIWGTEPN',
    suggestedConditions: {
      temperature_c: 50,
      ph: 6,
      salinity_m_m: 100,
      solvent_exposure: 'low',
      use_case: 'textile_biofuel',
    },
  },
  {
    id: 'lipase',
    label: 'Lipase B (CALB)',
    enzymeName: 'Lipase B',
    organism: 'Moesziomyces antarcticus (formerly Candida antarctica)',
    uniprotAccession: 'P41365',
    useCase: 'Food processing & biodiesel (ester/fat conversion)',
    description: 'One of the most widely used industrial lipases; catalyzes ester hydrolysis and transesterification for food processing and biodiesel production.',
    fastaHeader: '>sp|P41365|LIPB_MOEAN Lipase B OS=Moesziomyces antarcticus',
    sequence:
      'MKLLSLTGVAGVLATCVAATPLVKRLPSGSDPAFSQPKSVLDAGLTCQGASPSSVSKPIL' +
      'LVPGTGTTGPQSFDSNWIPLSTQLGYTPCWISPPPFMLNDTQVNTEYMVNAITALYAGSG' +
      'NNKLPVLTWSQGGLVAQWGLTFFPSIRSKVDRLMAFAPDYKGTVLAGPLDALAVSAPSVW' +
      'QQTTGSALTTALRNAGGLTQIVPTTNLYSATDEIVQPQVSNSPLDSSYLFNGKNVQAQAV' +
      'CGPLFVIDHAGSLTSQFSYVVGRSALRSTTGQARSADYGITDCNPLPANDLTPEQKVAAA' +
      'ALLAPAAAAIVAGPKQNCEPDLMPYARPFAVGKRTCSGIVTP',
    suggestedConditions: {
      temperature_c: 45,
      ph: 7.5,
      salinity_m_m: 50,
      solvent_exposure: 'high',
      use_case: 'food_processing',
    },
  },
  {
    id: 'amylase',
    label: 'Alpha-amylase',
    enzymeName: 'Alpha-amylase (AmyS)',
    organism: 'Bacillus licheniformis',
    uniprotAccession: 'P06278',
    useCase: 'Detergents & starch processing (starch breakdown)',
    description: 'Breaks down starch into smaller sugars; used in detergents to remove starch-based stains and in starch/food processing.',
    fastaHeader: '>sp|P06278|AMY_BACLI Alpha-amylase OS=Bacillus licheniformis',
    sequence:
      'MKQQKRLYARLLTLLFALIFLLPHSAAAAANLNGTLMQYFEWYMPNDGQHWKRLQNDSAY' +
      'LAEHGITAVWIPPAYKGTSQADVGYGAYDLYDLGEFHQKGTVRTKYGTKGELQSAIKSLH' +
      'SRDINVYGDVVINHKGGADATEDVTAVEVDPADRNRVISGEHRIKAWTHFHFPGRGSTYS' +
      'DFKWHWYHFDGTDWDESRKLNRIYKFQGKAWDWEVSNENGNYDYLMYADIDYDHPDVAAE' +
      'IKRWGTWYANELQLDGFRLDAVKHIKFSFLRDWVNHVREKTGKEMFTVAEYWQNDLGALE' +
      'NYLNKTNFNHSVFDVPLHYQFHAASTQGGGYDMRKLLNSTVVSKHPLKAVTFVDNHDTQP' +
      'GQSLESTVQTWFKPLAYAFILTRESGYPQVFYGDMYGTKGDSQREIPALKHKIEPILKAR' +
      'KQYAYGAQHDYFDHHDIVGWTREGDSSVANSGLAALITDGPGGAKRMYVGRQNAGETWHD' +
      'ITGNRSEPVVINSEGWGEFHVNGGSVSIYVQR',
    suggestedConditions: {
      temperature_c: 70,
      ph: 6.5,
      salinity_m_m: 150,
      solvent_exposure: 'low',
      use_case: 'detergent',
    },
  },
  {
    id: 'laccase',
    label: 'Laccase (CotA)',
    enzymeName: 'Laccase',
    organism: 'Bacillus subtilis',
    uniprotAccession: 'P07788',
    useCase: 'Pulp & paper, dye degradation',
    description: 'A copper-containing oxidase used in pulp bleaching, dye degradation, and other oxidative industrial processes.',
    fastaHeader: '>sp|P07788|COTA_BACSU Laccase OS=Bacillus subtilis',
    sequence:
      'MTLEKFVDALPIPDTLKPVQQSKEKTYYEVTMEECTHQLHRDLPPTRLWGYNGLFPGPTI' +
      'EVKRNENVYVKWMNNLPSTHFLPIDHTIHHSDSQHEEPEVKTVVHLHGGVTPDDSDGYPE' +
      'AWFSKDFEQTGPYFKREVYHYPNQQRGAILWYHDHAMALTRLNVYAGLVGAYIIHDPKEK' +
      'RLKLPSDEYDVPLLITDRTINEDGSLFYPSAPENPSPSLPNPSIVPAFCGETILVNGKVW' +
      'PYLEVEPRKYRFRVINASNTRTYNLSLDNGGDFIQIGSDGGLLPRSVKLNSFSLAPAERY' +
      'DIIIDFTAYEGESIILANSAGCGGDVNPETDANIMQFRVTKPLAQKDESRKPKYLASYPS' +
      'VQHERIQNIRTLKLAGTQDEYGRPVLLLNNKRWHDPVTETPKVGTTEIWSIINPTRGTHP' +
      'IHLHLVSFRVLDRRPFDIARYQESGELSYTGPAVPPPPSEKGWKDTIQAHAGEVLRIAAT' +
      'FGPYSGRYVWHCHILEHEDYDMMRPMDITDPHK',
    suggestedConditions: {
      temperature_c: 50,
      ph: 5,
      salinity_m_m: 50,
      solvent_exposure: 'low',
      use_case: 'pulp_paper',
    },
  },
];

export function getPresetById(id: string): EnzymePreset | undefined {
  return enzymePresets.find((preset) => preset.id === id);
}

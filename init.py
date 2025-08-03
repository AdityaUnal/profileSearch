import os
import json 
import requests
import re
import nltk
import heapq
import math
import numpy as np
import en_core_web_sm
from spacy.tokens import Doc
from spacy.language import Language
from sklearn.metrics.pairwise import cosine_similarity
import voyageai
from turbopuffer import Turbopuffer
import turbopuffer
import time
import concurrent.futures
from threading import Lock
import argparse
import requests
import json
import gzip

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# --------- Config --------- #
TURBOPUFFER_REGION = "aws-us-west-2"
TPUF_NAMESPACE_NAME = "aditya_unal"
TURBOPUFFER_API_KEY = os.getenv("TURBOPUFFER_API_KEY")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
TOTAL_BATCHES = 39
MAX_RETRIES = 10
NUM_THREADS = 5
STREAMING_ENDPOINT_BASE = "https://mercor-dev--search-eng-interview-documents.modal.run/stream_documents"
# Initialize Turbopuffer client
tpuf = turbopuffer.Turbopuffer(
    api_key=TURBOPUFFER_API_KEY,
    region=TURBOPUFFER_REGION,
)
ns = tpuf.namespace(TPUF_NAMESPACE_NAME)

# --------- Inserting in Turbopuffer --------- #

def fetch_and_upsert_batch(batch_number: int):
    endpoint = f"{STREAMING_ENDPOINT_BASE}/{batch_number}"
    logger.info(f"Fetching batch {batch_number} from: {endpoint}")

    try:
        response = requests.get(endpoint, stream=True, timeout=600)
        response.raise_for_status()

        batch = []

        # Collect all chunks of raw gzip data
        compressed_chunks = []
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if chunk:
                compressed_chunks.append(chunk)

        # Combine chunks and decompress
        compressed_data = b"".join(compressed_chunks)

        try:
            # Decompress the gzip data
            decompressed_data = gzip.decompress(compressed_data)

            # Process line by line
            for line in decompressed_data.decode("utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue

                try:
                    doc = json.loads(line)

                    # Check if it's an error message
                    if "error" in doc:
                        logger.error(
                            f"Error from batch {batch_number}: {doc['error']}")
                        break

                    # Skip documents without embeddings
                    if not doc.get("embedding"):
                        continue

                    profile = {
                        "id": str(doc.get("_id")),
                        "vector": doc.get("embedding", []),
                        "email": doc.get("email", ""),
                        "rerank_summary": doc.get("rerankSummary", ""),
                        "country": doc.get("country", ""),
                        "name": doc.get("name", ""),
                        "linkedin_id": doc.get("linkedinId", ""),
                        "highest_level": doc.get("education", {}).get("highest_level", ""),
                        "prestige_scores_education": [
                            degree.get("prestige_score")
                            for degree in doc.get("education", {}).get("degrees", [])
                            if degree.get("prestige_score") is not None
                        ],
                        "yearsOfWorkExperience" : doc.get("yearsOfWorkExperience",0),
                        "prestige_scores_work": [
                            experience.get("prestige_score")
                            for experience in doc.get("experience", {})
                            if experience.get("prestige_score") is not None
                        ],
                        "prestigeScore": doc.get("prestigeScore")
                    }

                    batch.append(profile)

                except json.JSONDecodeError as e:
                    logger.error(
                        f"JSON decode error in batch {batch_number}: {e}")
                    continue

        except gzip.BadGzipFile as e:
            logger.error(
                f"Gzip decompression error in batch {batch_number}: {e}")
            return 0

        if not batch:
            logger.info(
                f"No documents with embeddings found in batch {batch_number}")
            return 0

        if upsert_batch_to_turbopuffer(batch):
            logger.info(
                f"Successfully processed batch {batch_number}: {len(batch)} documents"
            )
            return len(batch)
        else:
            return 0

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching batch {batch_number}: {e}")
        return 0


def upsert_batch_to_turbopuffer(batch):
    for i in range(MAX_RETRIES):
        try:
            ns.write(
                upsert_rows=batch,
                distance_metric="cosine_distance",
                schema={
                    "id": "string",
                    "rerank_summary": {"type": "string", "full_text_search": True},
                    "email": "string",
                    "country": "string",
                    "name": "string",
                    "linkedin_id": "string",
                    "highest_level": "string",
                    "prestige_scores_education": "[]float",
                    "prestige_scores_work": "[]float",
                    "yearsOfWorkExperience": "float",
                    "prestigeScore" : "float"
                },
            )

            logger.info(
                f"Successfully upserted {len(batch)} documents to Turbopuffer")
            return True
        except Exception as e:
            logger.error(f"Error upserting batch to Turbopuffer: {e}")
            if i < MAX_RETRIES - 1:
                logger.info(f"Retrying in {i + 1} seconds...")
                time.sleep(i + 1)
            else:
                logger.error(
                    f"Turbopuffer upsert failed after {MAX_RETRIES} attempts")
                return False


def delete_namespace():
    try:
        ns.delete_all()
        logger.info("Namespace cleared successfully")
    except Exception as e:
        logger.error(f"Namespace already cleared")

# --------- NLP Setup --------- #
nlp = en_core_web_sm.load()

@Language.component("senticizer")
def senticizer(doc):
    text = re.sub(r'(\n)(-|[0-9])', r"\1\n\2", doc.text)[3:]
    parts = text.split('\n\n')
    tokens = [token for part in parts for token in nltk.word_tokenize(part)]
    return Doc(doc.vocab, words=tokens)

nlp.add_pipe("senticizer", before="tok2vec")

# --------- Clients --------- #
vo = voyageai.Client(api_key=VOYAGE_API_KEY)
tpuf = Turbopuffer(region=TURBOPUFFER_REGION, api_key=TURBOPUFFER_API_KEY)
ns = tpuf.namespace(TPUF_NAMESPACE_NAME)

# --------- Hard & Soft Criterias --------- #
hard_criterias = [
    '''
    1. JD degree from an accredited U.S. law school
    2. 3+ years of experience practicing law
    ''',
    '''
    1. 2-4 years of experience as a Corporate Lawyer at a leading law firm in the USA, Europe, or Canada, or in-house at a major global organization
    2. Graduate of a reputed law school in the USA, Europe, or Canada
    ''',
    '''
    1. MD degree from a medical school in the U.S. or India
    ''',
    '''
    1. MD degree from a top U.S. medical school
    2. 2+ years of clinical practice experience in the U.S.
    3. Experience working as a General Practitioner (GP)
    ''',
    '''
    1. Completed undergraduate studies in the U.S., U.K., or Canada
    2. PhD in Biology from a top U.S. university    
    ''',
    '''
    1. PhD (in progress or completed) from a distinguished program in sociology, anthropology, or economics
    2. PhD program started within the last 3 years
    ''',
    ''' 	
    1. Completed undergraduate studies in the U.S., U.K., or Canada
    2. PhD in Mathematics or Statistics from a top U.S. university
    ''',
    '''
    1. MBA from a Prestigious U.S. university (M7 MBA)
    2. 3+ years of experience in quantitative finance, including roles such as risk modeling, algorithmic trading, or financial engineering 
    ''',
    '''
    1. MBA from a U.S. university
    2. 2+ years of prior work experience in investment banking, corporate finance, or M&A advisory
    ''',
    '''
    1. Higher degree in Mechanical Engineering from an accredited university
    2. 3+ years of professional experience in mechanical design, product development, or systems engineering
    '''    
]

soft_criterias = [
    '''
    1. Experience advising clients on tax implications of corporate or financial transactions
    2. Experience handling IRS audits, disputes, or regulatory inquiries
    3. Experience drafting legal opinions or filings related to federal and state tax compliance
    ''',
    '''
    1. Experience supporting Corporate M&A transactions, including due diligence and legal documentation
    2. Experience drafting and negotiating legal contracts or commercial agreements
    3. Familiarity with international business law or advising on regulatory requirements across jurisdictions
    ''',
    '''
    1. Board certification in Radiology (ABR, FRCR, or equivalent) or comparable credential
    2. 3+ years of experience interpreting X-ray, CT, MRI, ultrasound, or nuclear medicine studies
    3. Expertise in radiology reporting, diagnostic protocols, differential diagnosis, or AI applications in medical imaging
    ''',
    '''
    1. Familiarity with EHR systems and managing high patient volumes in outpatient or family medicine settings
    2. Comfort with telemedicine consultations, patient triage, and interdisciplinary coordination
    ''',
    '''
    1. Research experience in molecular biology, genetics, or cell biology, with publications in peer-reviewed journals
    2. Familiarity with experimental design, data analysis, and lab techniques such as CRISPR, PCR, or sequencing
    3. Experience mentoring students, teaching undergraduate biology courses, or collaborating on interdisciplinary research
    ''',
    '''
    1. Demonstrated expertise in ethnographic methods, with substantial fieldwork or case study research involving cultural, social, or economic systems
    2. Strong academic output — published papers, working papers, or conference presentations on anthropological or sociological topics
    3. Experience applying anthropological theory to real-world or interdisciplinary contexts (e.g., migration, labor, technology, development), showing both conceptual depth and practical relevance
    ''',
    '''
    1. Research expertise in pure or applied mathematics, statistics, or probability, with peer-reviewed publications or preprints
    2. Proficiency in mathematical modeling, proof-based reasoning, or algorithmic problem-solving
    ''',
    '''
    1. Experience applying financial modeling techniques to real-world problems like portfolio optimization or derivatives pricing
    2. Proficiency with Python for quantitative analysis and exposure to financial libraries (e.g., QuantLib or equivalent)
    3. Demonstrated ability to work in high-stakes environments such as global investment firms, showing applied knowledge of quantitative methods in production settings
    ''',
    '''
    1. Specialized experience in healthcare-focused investment banking or private equity, including exposure to sub-verticals like biotech, pharma services, or provider networks
    2. Led or contributed to transactions involving healthcare M&A, recapitalizations, or growth equity investments
    3. Familiarity with healthcare-specific metrics, regulatory frameworks, and value creation strategies (e.g., payer-provider integration, RCM optimization)
    ''',
    '''
    1. Experience with CAD tools (e.g., SolidWorks, AutoCAD) and mechanical simulation tools (e.g., ANSYS, COMSOL)
    2. Demonstrated involvement in end-to-end product lifecycle — from concept through prototyping to manufacturing or testing
    3. Domain specialization in areas like thermal systems, fluid dynamics, structural analysis, or mechatronics
    '''
]

criterias = ["tax_lawyer.yml",
             "junior_corporate_lawyer.yml",
             "radiology.yml",
             "doctors_md.yml",
             "biology_expert.yml",
             "anthropology.yml",
             "mathematics_phd.yml",
             "quantitative_finance.yml",
             "bankers.yml",
             "mechanical_engineers.yml"]

# --------- Vector Generation --------- #
def generate_soft_vectors(soft_criterias):
    return [vo.embed(criteria, model="voyage-3").embeddings for criteria in soft_criterias]

# --------- Turbopuffer Retrieval --------- #
def retrieve_candidates(hard_criterias):
    vector_results = []
    for doc in hard_criterias:
        result = ns.query(
            rank_by=("rerank_summary", "BM25", doc),
            top_k=1000,
            include_attributes=["id", "name", "rerank_summary", "vector"]
        )
        vector_results.append([dict(row) for row in result.rows])
    return vector_results

# --------- Composite Scoring + Ranking --------- #
def bm25_rank_to_score(rank, decay=200):
    return math.exp(-rank / decay)

def rank_profiles(vector_results, soft_vectors, criterias, top_k=10):
    results = []
    for i, criteria in enumerate(soft_vectors):
        criteria = np.array(criteria)
        docs = vector_results[i]
        heap = []
        for rank, doc in enumerate(docs):
            cos_sim = (cosine_similarity(np.array(doc["vector"]).reshape(1, -1), criteria))


            metadata = {
                "id": doc["id"],
            }

            if len(heap) < top_k:
                heapq.heappush(heap, (cos_sim, metadata))
            else:
                heapq.heappushpop(heap, (cos_sim, metadata))
        results.append({
            "config_path" : criterias[i],
            "object_ids" : [ent[1]["id"] for ent in heap]})

    return results

# --------- Main --------- #
def main():
    parser = argparse.ArgumentParser(
        description="Batch endpoint to Turbopuffer migration tool"
    )
    parser.add_argument(
        "action",
        choices=["delete", "migrate"],
        help="Action to perform",
        default="migrate",
        nargs="?",
    )
    args = parser.parse_args()

    if args.action == "delete":
        logger.info("Clearing Turbopuffer namespace...")
        delete_namespace()
        exit()

    logger.info("Starting migration from batch endpoints to Turbopuffer")
    logger.info(f"Total batches to process: {TOTAL_BATCHES}")
    logger.info(f"Using {NUM_THREADS} threads")

    batch_numbers = list(range(0, TOTAL_BATCHES))

    total_processed = 0
    lock = Lock()

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        futures = [
            executor.submit(fetch_and_upsert_batch, batch_num)
            for batch_num in batch_numbers
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                batch_count = future.result()
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                batch_count = 0

            with lock:
                total_processed += batch_count
            logger.info(f"Total processed so far: {total_processed}")

    logger.info(
        f"Migration completed! Total documents processed: {total_processed}")
    soft_vectors = generate_soft_vectors(soft_criterias)
    vector_results = retrieve_candidates(hard_criterias)
    res = rank_profiles(vector_results, soft_vectors, criterias)
    return res

if __name__ == "__main__":
    results = main()
    payload = {entry["config_path"]: entry["object_ids"] for entry in results}
    for entry in results:
        payload ={
            "config_path":entry["config_path"],
            "object_ids":entry["object_ids"]
        }
        response = requests.post(
            "https://mercor-dev--search-eng-interview.modal.run/evaluate",
            headers={
                "Content-Type": "application/json",
                "Authorization": "unal.aditya10@gmail.com"
            },
            json=payload
        )

        # Print response
        sum = 0
        print(response.status_code)
        with open("response_output.txt", "a", encoding="utf-8") as f:
            f.write(response.text)

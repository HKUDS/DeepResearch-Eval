import json
from Atools import *
import hashlib
from tqdm import trange
import os
import glob
import argparse
import logging
import datetime
import time
import hashlib
from typing import Optional, Dict, List, Tuple

# Logging configuration
log_path = './exp/judge.txt'
progress_log_path = './exp/judge.json'
if not os.path.exists(log_path):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
if not os.path.exists(progress_log_path):
    os.makedirs(os.path.dirname(progress_log_path), exist_ok=True)

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CheckpointManager:
    """Checkpoint Manager"""
    
    def __init__(self, checkpoint_file: str = 'checkpoint.json'):
        self.checkpoint_file = checkpoint_file
        self.checkpoint_data = self.load_checkpoint()
    
    def load_checkpoint(self) -> Dict:
        """Load checkpoint data"""
        try:
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded checkpoint data: {data}")
                    return data
        except Exception as e:
            logger.warning(f"Failed to load checkpoint file: {e}")
        return {
            'processed_files': [],
            'current_index': 0,
            'start_time': None,
            'total_files': 0
        }
    
    def save_checkpoint(self, processed_files: List[str], current_index: int, total_files: int):
        """Save checkpoint data"""
        checkpoint_data = {
            'processed_files': processed_files,
            'current_index': current_index,
            'start_time': datetime.datetime.now().isoformat(),
            'total_files': total_files
        }
        try:
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved checkpoint: processed {len(processed_files)} files, current index: {current_index}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint file: {e}")
    
    def is_file_processed(self, file_id: str) -> bool:
        """Check whether the file has been processed"""
        return file_id in self.checkpoint_data.get('processed_files', [])
    
    def add_processed_file(self, file_id: str):
        """Add processed file"""
        if 'processed_files' not in self.checkpoint_data:
            self.checkpoint_data['processed_files'] = []
        if file_id not in self.checkpoint_data['processed_files']:
            self.checkpoint_data['processed_files'].append(file_id)
    
    def get_progress(self) -> Tuple[int, int]:
        """Get progress information"""
        processed = len(self.checkpoint_data.get('processed_files', []))
        total = self.checkpoint_data.get('total_files', 0)
        return processed, total

def log_progress(message: str, level: str = 'info'):
    """Record progress logs"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    
    if level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'debug':
        logger.debug(message)
    
    # Also write to the progress log file
    try:
        with open(progress_log_path, 'a', encoding='utf-8') as f:
            f.write(f"{log_message}\n")
    except Exception as e:
        logger.error(f"Failed to write progress log: {e}")

def extract_quality_scores(use_topic, use_report, max_attempts, debug_mode):
    """
    Extract quality scores of the report.
    Args:
        use_topic: topic content
        use_report: report content
        max_attempts: maximum retry attempts
        debug_mode: whether in debug mode
    Returns:
        comprehensiveness_score, coherence_score, clarity_score, insight_score, overall_score, quality_reason
    """
    attempt = 0
    while attempt < max_attempts:
        try:
            log_progress(f"Start extracting quality scores, attempt: {attempt + 1}/{max_attempts}", 'debug')
            judge_quality_result = judge_quality(use_topic, use_report)
            comprehensiveness_score = judge_quality_result['Comprehensiveness_Score']
            coherence_score = judge_quality_result['Coherence_Score']
            clarity_score = judge_quality_result['Clarity_Score']
            insight_score = judge_quality_result['Insightfulness_Score']
            overall_score = judge_quality_result['Overall_Score']
            quality_reason = judge_quality_result['Reason']
            log_progress(f"Quality score extraction succeeded", 'debug')
            return comprehensiveness_score, coherence_score, clarity_score, insight_score, overall_score, quality_reason
        except Exception as e:
            attempt += 1
            log_progress(f"Quality score extraction failed, attempt: {attempt}/{max_attempts}, error: {e}", 'warning')
            if attempt == max_attempts:
                log_progress(f"Quality score extraction ultimately failed: {e}", 'error')
                return None, None, None, None, None, None
            else:
                time.sleep(2)  # Wait 2 seconds before retrying
                continue

def extract_repeatability_scores(passage1, passage2, max_attempts, debug_mode):
    """
    Extract repeatability score for two passages.
    Args:
        passage1: first passage
        passage2: second passage
        max_attempts: maximum retry attempts
        debug_mode: whether in debug mode
    Returns:
        repeatability_score, repeatability_explanation, repetitions_found, repeatability_confidence
    """
    attempt = 0
    while attempt < max_attempts:   
        try:
            log_progress(f"Start extracting repeatability score, attempt: {attempt + 1}/{max_attempts}", 'debug')
            judge_repeatability_result = judge_repeatability_pair(passage1, passage2)
            repeatability_score = judge_repeatability_result['score']
            repeatability_explanation = judge_repeatability_result['explanation']
            repetitions_found = judge_repeatability_result['repetitions_found']
            repeatability_confidence = judge_repeatability_result['confidence']
            log_progress(f"Repeatability score extraction succeeded", 'debug')
            return repeatability_score, repeatability_explanation, repetitions_found, repeatability_confidence
        except Exception as e:
            attempt += 1
            log_progress(f"Repeatability score extraction failed, attempt: {attempt}/{max_attempts}, error: {e}", 'warning')
            try:
                judge_repeatability_result = judge_repeatability_result[-1]
                repeatability_score = judge_repeatability_result['score']
                repeatability_explanation = judge_repeatability_result['explanation']
                repetitions_found = judge_repeatability_result['repetitions_found']
                repeatability_confidence = judge_repeatability_result['confidence']
                log_progress(f"Repeatability score extraction succeeded (fallback)", 'debug')
                return repeatability_score, repeatability_explanation, repetitions_found, repeatability_confidence
            except Exception as e:
                if attempt == max_attempts:
                    log_progress(f"Repeatability score extraction ultimately failed: {e}", 'error')
                    return None, None, None, None
                else:
                    time.sleep(2)  # Wait 2 seconds before retrying
                    continue

def judge_one_report(
    use_topic,
    use_report,
    headings, 
    sections, 
    sections_headings, 
    sections_with_headings,
    repeat_nums = 30,
    max_attempts = 3,
    file_id = None,
    debug_mode = True,
):
    """
    Evaluate a single report for quality and repeatability.
    Args:
        use_topic: topic content
        use_report: report content
        headings: list of first-level headings
        sections: section contents
        sections_headings: section headings
        sections_with_headings: sections with headings
        repeat_nums: number of pairs for repeatability checks
        max_attempts: maximum retry attempts
        file_id: file id (optional)
        debug_mode: whether in debug mode
    Returns:
        result_entry: dict containing various scores and repeatability results
    """
    
    log_progress(f"Start processing file: {file_id}", 'info')

    result_entry = {
        'file_id': file_id,
        'topic': use_topic,
        'compare_list': [],
        'repeat_results': [],
        'comprehensiveness_score': None,
        'coherence_score': None,
        'clarity_score': None,
        'insight_score': None,
        'overall_score': None,
        'repeat_score': None,
        'quality_reason': None
    }
    ERRFLAG = False
    
    if debug_mode:
        log_progress('Start extracting quality scores', 'debug')
    comprehensiveness_score, coherence_score, clarity_score, insight_score, overall_score, quality_reason = extract_quality_scores(use_topic, use_report, max_attempts, debug_mode)
    if comprehensiveness_score is None:
        ERRFLAG = True
        log_progress(f"Quality score extraction failed, file: {file_id}", 'error')
    
    if debug_mode:
        log_progress('Start extracting repeatability scores', 'debug')
    pair_list = []
    label_list = []
    repeat_score = 0
    repeat_num = 0
    sections_with_headings = [section for section in sections_with_headings if 'https' not in section]
    # Filter out paragraphs that are too short
    min_length = 200
    sections_with_headings = [section for section in sections_with_headings if len(section) >= min_length]
    results = generate_random_pair_with_label(sections_with_headings[1:-1], pair_nums=repeat_nums)
    
    return_results = []
    compare_list = []
    
    log_progress(f"Start processing {len(results)} text pairs for repeatability checks", 'debug')
    for i, (pairs, label, _) in enumerate(results):
        if label == -2:
            passage1 = sections_with_headings[1:][pairs[0]]
            passage2 = sections_with_headings[1:][pairs[1]]
            repeatability_score = None
            repeatability_score, repeatability_explanation, repetitions_found, repeatability_confidence = extract_repeatability_scores(
                    passage1, passage2, max_attempts, debug_mode)
            if repeatability_score is None:
                log_progress(f"Repeatability scoring failed for pair {i+1}", 'warning')
                continue
            else:
                compare_list.append((passage1, passage2, repeatability_score))
                repeat_score += repeatability_score
                repeat_num += 1
                return_results.append((passage1, passage2, repeatability_score, repeatability_explanation, repetitions_found, repeatability_confidence))
                log_progress(f"Repeatability scoring succeeded for pair {i+1}: {repeatability_score}", 'debug')
        else:
            continue
    
    if len(return_results) == 0:
        ERRFLAG = True
        log_progress(f"All repeatability checks failed, file: {file_id}", 'error')
    
    if ERRFLAG:
        log_progress(f"File processing failed: {file_id}", 'error')
        return None
    else:
        avg_repeat_score = repeat_score / repeat_num if repeat_num > 0 else 0
        result_entry = {
            'file_id': file_id,
            'topic': use_topic,
            'compare_list': compare_list,
            'repeat_results': return_results,
            'comprehensiveness_score': comprehensiveness_score,
            'coherence_score': coherence_score,
            'clarity_score': clarity_score,
            'insight_score': insight_score,
            'overall_score': overall_score,
            'repeat_score': avg_repeat_score,
            'quality_reason': quality_reason
        }
        log_progress(f"File processed successfully: {file_id}, quality score: {overall_score}, repeatability score: {avg_repeat_score}", 'info')
        return result_entry

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputpath', type=str)
    parser.add_argument('--outputpath', type=str)
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--clear_checkpoint', action='store_true', help='Clear checkpoint file')
    args = parser.parse_args()
    
    
    # Initialize checkpoint manager
    checkpoint_manager = CheckpointManager()
    
    # If clear_checkpoint is specified, delete checkpoint file
    if args.clear_checkpoint:
        if os.path.exists(checkpoint_manager.checkpoint_file):
            os.remove(checkpoint_manager.checkpoint_file)
            log_progress("Checkpoint file cleared", 'info')
        checkpoint_manager = CheckpointManager()
    
    SAVEPATH = args.outputpath
        
    if not os.path.exists(SAVEPATH):
        os.makedirs(SAVEPATH)
        log_progress(f"Created output directory: {SAVEPATH}", 'info')
    
    all_json_data = []
    with open(args.inputpath, 'r', encoding='utf-8') as file:
        for line in file:
            all_json_data.append(json.loads(line))
        
    # Update checkpoint data
    checkpoint_manager.checkpoint_data['processed_files'] = []
    checkpoint_manager.checkpoint_data['current_index'] = 0
    checkpoint_manager.checkpoint_data['total_files'] = len(all_json_data)
    
    # Get processed file list
    processed_files = checkpoint_manager.checkpoint_data.get('processed_files', [])
    current_index = checkpoint_manager.checkpoint_data.get('current_index', 0)
    
    log_progress(f"Start processing: total files: {len(all_json_data)}, processed: {len(processed_files)}, current index: {current_index}", 'info')
    
    # Use tqdm to show progress
    for i, json_data in enumerate(all_json_data):
        EN_topic = json_data['topic']

        file_id = hashlib.md5(EN_topic.encode('utf-8')).hexdigest()
        
        # Check if already processed
        if file_id in processed_files:
            log_progress(f"File already processed, skip: {file_id}", 'debug')
            continue
        
        log_progress(f"Processing file {i+1}/{len(all_json_data)}: {file_id}", 'info')
        
        EN_report = json_data['report']
        
        paragraphs = split_paragraphs(EN_report)
        if len(paragraphs) <= 3:
            continue

        try:
            headings, sections, sections_headings, sections_with_headings = extract_first_level_headings(EN_report)
            sections_with_headings = sections_with_headings[1:-1]
            use_report = EN_report
            use_topic = EN_topic
        except Exception as e:
            log_progress(f"Failed to extract headings, file: {file_id}, error: {e}", 'error')
            continue

        result_entry = judge_one_report(
            use_topic,
            use_report,
            headings, 
            sections, 
            sections_headings, 
            sections_with_headings,
            repeat_nums=30,
            max_attempts=3,
            file_id=file_id,
            debug_mode=True,
        )
        
        if result_entry is not None:
            # Save result
            output_file = os.path.join(SAVEPATH, f'{file_id}.json')
            try:
                with open(output_file, 'w', encoding='utf-8') as file:
                    json.dump(result_entry, file, indent=4, ensure_ascii=False)
                log_progress(f"Result saved: {output_file}", 'debug')
                
                # Update checkpoint
                checkpoint_manager.add_processed_file(file_id)
                checkpoint_manager.save_checkpoint(
                    processed_files=checkpoint_manager.checkpoint_data['processed_files'],
                    current_index=i,
                    total_files=len(all_json_data)
                )
            except Exception as e:
                log_progress(f"Failed to save result: {output_file}, error: {e}", 'error')
        else:
            log_progress(f"Processing failed, skip saving: {file_id}", 'warning')
    
    # Processing complete
    processed_count, total_count = checkpoint_manager.get_progress()
    log_progress(f"Completed. Total files: {total_count}, successfully processed: {processed_count}", 'info')

if __name__ == '__main__':
    main()
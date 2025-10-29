"""
Jobs API client for tracking job status in Mammoth.
"""

from typing import Optional, Dict, Any, List, Union


class JobsAPI:
    """Client for interacting with Mammoth Jobs API."""
    
    def __init__(self, client):
        self._client = client
    
    def get_job(
        self,
        job_id: int,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Get job status by ID.
        
        Args:
            job_id: ID of the job to track
            timeout: Timeout for the request (unused, kept for compatibility)
            
        Returns:
            Dict containing job information including status, response, timestamps
            
        Raises:
            MammothAPIError: If the API request fails
        """
        workspace_id = self._client.workspace_id
        
        headers = {"x-workspace-id": str(workspace_id)}
        
        response = self._client._request(
            "GET",
            f"/jobs/{job_id}",
            headers=headers
        )
        return response
    
    def get_jobs(
        self,
        job_ids: Union[List[int], str]
    ) -> Dict[str, Any]:
        """
        Track multiple job IDs.
        
        Args:
            job_ids: List of job IDs or comma-separated string of job IDs
            
        Returns:
            Dict containing jobs list with status information
            
        Raises:
            MammothAPIError: If the API request fails
        """
        workspace_id = self._client.workspace_id
        
        # Convert list to comma-separated string if needed
        if isinstance(job_ids, list):
            job_ids_str = ",".join(str(job_id) for job_id in job_ids)
        else:
            job_ids_str = str(job_ids)
        
        params = {
            "job_ids": j
        }
        
        headers = {"x-workspace-id": str(workspace_id)}
        
        response = self._client._request(
            "GET",
            "/jobs",
            params=params,
            headers=headers
        )
        return response
    
    def wait_for_job(
        self,
        job_id: int,
        timeout: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for a job to complete and return the result.
        
        Args:
            job_id: ID of the job to wait for
            timeout: Maximum time to wait in seconds (default: 300)
            poll_interval: Time between polling attempts in seconds (default: 2)
            
        Returns:
            Dict containing the completed job information
            
        Raises:
            ValueError: If job fails or times out
            MammothAPIError: If the API request fails
        """
        import time
        
        workspace_id = self._client.workspace_id
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            job_response = self.get_job(job_id)
            
            # Extract job from response
            if 'job' in job_response:
                job = job_response['job']
            else:
                job = job_response
            
            status = job.get('status')
            
            if status == 'success':
                return job
            elif status in ['failure', 'error']:
                error_msg = job.get('response', {}).get('error', 'Job failed')
                raise ValueError(f"Job {job_id} failed: {error_msg}")
            elif status == 'processing':
                # Job still running, continue polling
                time.sleep(poll_interval)
            else:
                # Unknown status, continue polling
                time.sleep(poll_interval)
        
        # Timeout reached
        raise ValueError(f"Job {job_id} timed out after {timeout} seconds")
    
    def wait_for_jobs(
        self,
        job_ids: Union[List[int], str],
        timeout: int = 300,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for multiple jobs to complete.
        
        Args:
            job_ids: List of job IDs or comma-separated string
            timeout: Maximum time to wait in seconds (default: 300)
            poll_interval: Time between polling attempts in seconds (default: 2)
            
        Returns:
            Dict containing all completed jobs information
            
        Raises:
            ValueError: If any job fails or times out
            MammothAPIError: If the API request fails
        """
        import time
        
        # Convert to list if string
        if isinstance(job_ids, str):
            job_ids_list = [int(x.strip()) for x in job_ids.split(',')]
        else:
            job_ids_list = job_ids
        
        start_time = time.time()
        completed_jobs = {}
        
        while time.time() - start_time < timeout:
            jobs_response = self.get_jobs(job_ids_list)
            jobs = jobs_response.get('jobs', [])
            
            all_completed = True
            
            for job in jobs:
                job_id = job.get('id')
                status = job.get('status')
                
                if status == 'success':
                    completed_jobs[job_id] = job
                elif status in ['failure', 'error']:
                    error_msg = job.get('response', {}).get('error', 'Job failed')
                    raise ValueError(f"Job {job_id} failed: {error_msg}")
                elif status == 'processing':
                    all_completed = False
                else:
                    all_completed = False
            
            if all_completed:
                return {'jobs': list(completed_jobs.values())}
            
            time.sleep(poll_interval)
        
        # Timeout reached
        raise ValueError(f"Jobs {job_ids_list} timed out after {timeout} seconds")
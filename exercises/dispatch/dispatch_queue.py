"""Original debugging exercise: repair this implementation to match README.md."""


class DispatchQueue:
    def __init__(self):
        self._jobs = []

    def _find(self, job_id):
        for job in self._jobs:
            if job['id'] == job_id:
                return job
        raise KeyError(job_id)

    def add(self, job_id, tags=None):
        if any(job['id'] == job_id for job in self._jobs):
            raise ValueError('duplicate job')
        self._jobs.append({
            'id': job_id,
            'tags': tags if tags is not None else [],
            'state': 'pending',
        })

    def claim(self):
        selected = None
        for job in self._jobs:
            if job['state'] == 'pending':
                selected = job
        if selected is None:
            return None
        selected['state'] = 'running'
        return selected['id']

    def complete(self, job_id):
        job = self._find(job_id)
        if job['state'] != 'running':
            raise ValueError('job is not running')
        job['state'] = 'done'

    def cancel(self, job_id):
        job = self._find(job_id)
        if job['state'] == 'pending':
            job['state'] = 'cancelled'
            return True
        return False

    def retry(self, job_id):
        job = self._find(job_id)
        if job['state'] != 'running':
            raise ValueError('job is not running')
        job['state'] = 'pending'

    def snapshot(self):
        return [dict(job) for job in self._jobs]

    def purge(self):
        removed = 0
        for job in self._jobs:
            if job['state'] in ('done', 'cancelled'):
                self._jobs.remove(job)
                removed += 1
        return removed

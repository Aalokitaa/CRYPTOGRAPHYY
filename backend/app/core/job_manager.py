"""
CryptoScope Job Manager & Real-Time Streaming Bus
Tracks background analysis and training tasks in SQLite and broadcasts
real-time log and stepper progress updates via WebSockets and SSE.
"""

import asyncio
import json
import datetime
from typing import Dict, List, Optional, Any, Set
from fastapi import WebSocket
from backend.app.core.database import SessionLocal
from backend.app.core.models import JobModel

class JobManager:
    def __init__(self):
        # Maps job_id -> set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    def create_job(self, job_id: str, job_type: str, initial_step: str = "Initialized") -> JobModel:
        db = SessionLocal()
        try:
            job = JobModel(
                id=job_id,
                job_type=job_type,
                status="running",
                progress=0,
                step=initial_step,
                message="Job queued and processing started.",
                logs_json=json.dumps([f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {initial_step}"])
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job
        finally:
            db.close()

    async def update_job(self, 
                         job_id: str, 
                         progress: int, 
                         step: str, 
                         message: str, 
                         status: Optional[str] = None,
                         result_id: Optional[str] = None,
                         error: Optional[str] = None):
        db = SessionLocal()
        log_entry = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {step}: {message}"
        try:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if job:
                job.progress = progress
                job.step = step
                job.message = message
                if status:
                    job.status = status
                if result_id:
                    job.result_id = result_id
                if error:
                    job.error = error

                logs = json.loads(job.logs_json) if job.logs_json else []
                logs.append(log_entry)
                job.logs_json = json.dumps(logs)

                db.commit()
        finally:
            db.close()

        # Broadcast update to connected WebSockets
        await self.broadcast(job_id, {
            "job_id": job_id,
            "progress": progress,
            "step": step,
            "message": message,
            "status": status or "running",
            "log": log_entry,
            "result_id": result_id,
            "error": error
        })

    async def register_websocket(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        self.active_connections[job_id].add(websocket)

        # Send current status
        db = SessionLocal()
        try:
            job = db.query(JobModel).filter(JobModel.id == job_id).first()
            if job:
                await websocket.send_text(json.dumps({
                    "job_id": job.id,
                    "progress": job.progress,
                    "step": job.step,
                    "message": job.message,
                    "status": job.status,
                    "logs": json.loads(job.logs_json) if job.logs_json else [],
                    "result_id": job.result_id,
                    "error": job.error
                }))
        finally:
            db.close()

    def unregister_websocket(self, job_id: str, websocket: WebSocket):
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def broadcast(self, job_id: str, data: Dict[str, Any]):
        if job_id in self.active_connections:
            disconnected = []
            msg = json.dumps(data)
            for ws in self.active_connections[job_id]:
                try:
                    await ws.send_text(msg)
                except Exception:
                    disconnected.append(ws)
            for ws in disconnected:
                self.active_connections[job_id].discard(ws)

job_manager = JobManager()

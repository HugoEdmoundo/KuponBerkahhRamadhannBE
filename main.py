from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from scalar_fastapi import get_scalar_api_reference
from app.routers import periodes, registrations, queue_settings
from app.routers.queue_management import router as queue_router
from app.websocket import manager
from app.database import init_database
from app.exceptions import QueueAPIException, queue_exception_handler
import uvicorn

app = FastAPI(title="Queue Management API", description="Professional API modular structure", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
                   allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], allow_headers=["*"])

app.include_router(periodes.router, prefix="/api", tags=["periodes"])
app.include_router(registrations.router, prefix="/api", tags=["registrations"])
app.include_router(queue_settings.router, prefix="/api", tags=["queue-settings"])
app.include_router(queue_router, prefix="/api")

app.add_exception_handler(QueueAPIException, queue_exception_handler)

@app.get("/scalar")
def get_scalar():
    return get_scalar_api_reference(openapi_url=app.openapi_url, title=app.title)

@app.get("/")
def root():
    return {"message": "Queue Management API", "version": "1.0.0", "docs": "/scalar", "structure": "modular"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

init_database()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

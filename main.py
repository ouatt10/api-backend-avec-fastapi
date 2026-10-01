from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from config import settings
from database import Base, engine, get_db
import models  # noqa: F401 — nécessaire pour enregistrer les tables dans Base.metadata
from schemas import (
    TontineCreate,
    TontineResponse,
    MemberCreate,
    MemberResponse,
    ContributionCreate,
    ContributionResponse,
)

app = FastAPI(title=settings.app_name, debug=settings.debug)

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": settings.app_name}


# 1. Créer une tontine
@app.post("/tontines", response_model=TontineResponse)
def create_tontine(
    tontine: TontineCreate,
    db: Session = Depends(get_db)
):
    new_tontine = models.Tontine(
        name=tontine.name,
        contribution_amount=tontine.contribution_amount,
        number_of_rounds=tontine.number_of_rounds,
    )

    db.add(new_tontine)
    db.commit()
    db.refresh(new_tontine)

    return new_tontine


# 2. Ajouter un membre
@app.post(
    "/tontines/{tontine_id}/members",
    response_model=MemberResponse
)
def add_member(
    tontine_id: int,
    member: MemberCreate,
    db: Session = Depends(get_db),
):
    tontine = db.get(models.Tontine, tontine_id)

    if not tontine:
        raise HTTPException(
            status_code=404,
            detail="Tontine introuvable"
        )

    existing_position = (
        db.query(models.Member)
        .filter(
            models.Member.tontine_id == tontine_id,
            models.Member.position == member.position
        )
        .first()
    )

    if existing_position:
        raise HTTPException(
            status_code=400,
            detail=f"La position {member.position} est déjà utilisée par un autre membre"
        )

    new_member = models.Member(
        tontine_id=tontine_id,
        name=member.name,
        phone=member.phone,
        position=member.position,
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return new_member


# 3. Démarrer la tontine
@app.post("/tontines/{tontine_id}/start")
def start_tontine(
    tontine_id: int,
    db: Session = Depends(get_db),
):
    tontine = db.get(models.Tontine, tontine_id)

    if not tontine:
        raise HTTPException(
            status_code=404,
            detail="Tontine introuvable"
        )

    members = (
        db.query(models.Member)
        .filter(models.Member.tontine_id == tontine_id)
        .order_by(models.Member.position)
        .all()
    )

    if len(members) != tontine.number_of_rounds:
        raise HTTPException(
            status_code=400,
            detail="Le nombre de membres doit correspondre au nombre de tours"
        )

    if tontine.status != "CREATED":
        raise HTTPException(
            status_code=400,
            detail="La tontine est déjà démarrée"
        )

    for index, member in enumerate(members, start=1):
        new_round = models.Round(
            tontine_id=tontine_id,
            round_number=index,
            beneficiary_id=member.id,
            status="OPEN",
        )
        db.add(new_round)

    tontine.status = "STARTED"

    db.commit()

    return {
        "message": "Tontine démarrée",
        "tontine_id": tontine_id,
        "status": tontine.status,
    }


# 4. Enregistrer une cotisation
@app.post(
    "/tontines/{tontine_id}/rounds/{round_id}/contributions",
    response_model=ContributionResponse
)
def add_contribution(
    tontine_id: int,
    round_id: int,
    contribution: ContributionCreate,
    db: Session = Depends(get_db),
):
    tontine = db.get(models.Tontine, tontine_id)
    round_ = db.get(models.Round, round_id)

    if not tontine or not round_:
        raise HTTPException(
            status_code=404,
            detail="Tontine ou tour introuvable"
        )

    if round_.tontine_id != tontine_id:
        raise HTTPException(
            status_code=400,
            detail="Ce tour n'appartient pas à cette tontine"
        )

    member = db.get(models.Member, contribution.member_id)

    if not member or member.tontine_id != tontine_id:
        raise HTTPException(
            status_code=400,
            detail="Membre invalide"
        )

    new_contribution = models.Contribution(
        round_id=round_id,
        member_id=contribution.member_id,
        amount=contribution.amount,
    )

    db.add(new_contribution)
    db.commit()
    db.refresh(new_contribution)

    return new_contribution


# 5. Clôturer un tour
@app.post("/tontines/{tontine_id}/rounds/{round_id}/close")
def close_round(
    tontine_id: int,
    round_id: int,
    db: Session = Depends(get_db),
):
    round_ = db.get(models.Round, round_id)

    if not round_ or round_.tontine_id != tontine_id:
        raise HTTPException(
            status_code=404,
            detail="Tour introuvable"
        )

    if round_.status == "CLOSED":
        raise HTTPException(
            status_code=400,
            detail="Le tour est déjà clôturé"
        )

    round_.status = "CLOSED"
    round_.closed_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Tour clôturé",
        "round_id": round_id,
        "status": round_.status,
    }


# 6. Consulter la situation
@app.get("/tontines/{tontine_id}/situation")
def get_situation(
    tontine_id: int,
    db: Session = Depends(get_db),
):
    tontine = db.get(models.Tontine, tontine_id)

    if not tontine:
        raise HTTPException(
            status_code=404,
            detail="Tontine introuvable"
        )

    members = (
        db.query(models.Member)
        .filter(models.Member.tontine_id == tontine_id)
        .order_by(models.Member.position)
        .all()
    )

    rounds = (
        db.query(models.Round)
        .filter(models.Round.tontine_id == tontine_id)
        .order_by(models.Round.round_number)
        .all()
    )

    situation_rounds = []

    for round_ in rounds:
        contributions = (
            db.query(models.Contribution)
            .filter(models.Contribution.round_id == round_.id)
            .all()
        )

        total = sum(float(c.amount) for c in contributions)

        situation_rounds.append({
            "round_id": round_.id,
            "round_number": round_.round_number,
            "beneficiary_id": round_.beneficiary_id,
            "status": round_.status,
            "total_contributions": total,
        })

    return {
        "tontine": {
            "id": tontine.id,
            "name": tontine.name,
            "contribution_amount": float(tontine.contribution_amount),
            "number_of_rounds": tontine.number_of_rounds,
            "status": tontine.status,
        },
        "members": [
            {
                "id": member.id,
                "name": member.name,
                "phone": member.phone,
                "position": member.position,
            }
            for member in members
        ],
        "rounds": situation_rounds,
    }
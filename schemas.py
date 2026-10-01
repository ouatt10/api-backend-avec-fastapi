from pydantic import BaseModel

#creation de la classe TontineCreate qui hérite de BaseModel et contient les champs name, contribution_amount et number_of_rounds
class TontineCreate(BaseModel):
    name: str
    contribution_amount: float
    number_of_rounds: int

#creation de la classe TontineResponse qui hérite de TontineCreate et ajoute les champs id et status
class TontineResponse(TontineCreate):
    id: int
    status: str

    class Config:
        from_attributes = True


#creration de la classe RoundCreate qui hérite de BaseModel et contient les champs tontine_id, round_number et beneficiary_id
class MemberCreate(BaseModel):
    name: str
    phone: str
    position: int

#creation de la classe MemberResponse qui hérite de MemberCreate et ajoute les champs id et tontine_id
class MemberResponse(MemberCreate):
    id: int
    tontine_id: int

    class Config:
        from_attributes = True

#creation de la classe ContributionCreate qui hérite de BaseModel et contient les champs member_id et amount
class ContributionCreate(BaseModel):
    member_id: int
    amount: float

#creation de la classe ContributionResponse qui hérite de ContributionCreate et ajoute les champs id et round_id
class ContributionResponse(ContributionCreate):
    id: int
    round_id: int

    class Config:
        from_attributes = True


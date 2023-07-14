from flask_openapi3 import OpenAPI, Info, Tag
from flask import redirect
from urllib.parse import unquote

from sqlalchemy.exc import IntegrityError

from model import Session, Pet, Contato, TipoAnimal, TipoContato
from logger import logger
from schemas import *
from flask_cors import CORS

from schemas.tipoanimal import apresenta_tipos_animal
from schemas.tipocontato import ListagemTiposContatoSchema, apresenta_tipos_contato

info = Info(title="Clínica Veterinária API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

home_tag = Tag(name="Documentação", description="Seleção de documentação: Swagger, Redoc ou RapiDoc")
pet_tag = Tag(name="Pet", description="Adição, visualização e remoção de pets à base")
tipo_animal_tag = Tag(name="Tipo Animal", description="Busca do tipo de pet")
tipo_contato_tag = Tag(name="Tipo Contato", description="Busca do tipo de contato")
contato_tag = Tag(name="Contato Responsável", description="Adição de uma lista de contatos do resposável à um pet cadastrado na base")

@app.get('/', tags=[home_tag])
def home():
    """Redireciona para /openapi, tela que permite a escolha do estilo de documentação.
    """
    return redirect('/openapi')


@app.post('/pet', tags=[pet_tag],
          responses={"200": PetViewSchema, "409": ErrorSchema, "400": ErrorSchema})
def add_pet(form: PetSchema):
    """Adiciona um novo pet à base de dados

    Retorna uma representação dos pets e comentários associados.
    """
    pet = Pet(
        nome=form.nome,
        quantidade=form.quantidade,
        valor=form.valor)
    logger.debug(f"Adicionando pet de nome: '{pet.nome}'")
    try:
        session = Session()
        session.add(pet)
        session.commit()
        logger.debug(f"Adicionado pet de nome: '{pet.nome}'")
        return apresenta_pet(pet), 200

    except IntegrityError as e:
        error_msg = "Pet de mesmo nome e tipo já salvo na base :/"
        logger.warning(f"Erro ao adicionar pet ({pet.tipo})'{pet.nome}', {error_msg}")
        return {"mesage": error_msg}, 409

    except Exception as e:
        error_msg = "Não foi possível salvar novo item :/"
        logger.warning(f"Erro ao adicionar pet '{pet.nome}', {error_msg}")
        return {"mesage": error_msg}, 400


@app.get('/pets', tags=[pet_tag],
         responses={"200": ListagemPetsSchema, "404": ErrorSchema})
def get_pets():
    """Faz a busca por todos os pets cadastrados

    Retorna uma representação da listagem de pets.
    """
    logger.debug(f"Coletando pets ")
    session = Session()
    pets = session.query(Pet).all()

    if not pets:
        return {"pets": []}, 200
    else:
        logger.debug(f"%d pets encontrados" % len(pets))
        print(pets)
        return apresenta_pets(pets), 200


@app.get('/pet', tags=[pet_tag],
         responses={"200": PetViewSchema, "404": ErrorSchema})
def get_pet(query: PetBuscaSchema):
    """Faz a busca por um Pet a partir do id do pet

    Retorna uma representação dos pets e comentários associados.
    """
    pet_id = query.id
    logger.debug(f"Coletando dados sobre pet #{pet_id}")
    # criando conexão com a base
    session = Session()
    # fazendo a busca
    pet = session.query(Pet).filter(Pet.id == pet_id).first()

    if not pet:
        # se o pet não foi encontrado
        error_msg = "Pet não encontrado na base :/"
        logger.warning(f"Erro ao buscar pet '{pet_id}', {error_msg}")
        return {"message": error_msg}, 404
    else:
        logger.debug(f"Pet econtrado: '{pet.nome}'")
        # retorna a representação de pet
        return apresenta_pet(pet), 200


@app.delete('/pet', tags=[pet_tag],
            responses={"200": PetDelSchema, "404": ErrorSchema})
def del_pet(query: PetBuscaSchema):
    """Deleta um Pet a partir do nome de pet informado

    Retorna uma mensagem de confirmação da remoção.
    """
    pet_nome = unquote(unquote(query.nome))
    print(pet_nome)
    logger.debug(f"Deletando dados sobre pet #{pet_nome}")
    # criando conexão com a base
    session = Session()
    # fazendo a remoção
    count = session.query(Pet).filter(Pet.nome == pet_nome).delete()
    session.commit()

    if count:
        # retorna a representação da mensagem de confirmação
        logger.debug(f"Deletado pet #{pet_nome}")
        return {"mesage": "Pet removido", "id": pet_nome}
    else:
        # se o pet não foi encontrado
        error_msg = "Pet não encontrado na base :/"
        logger.warning(f"Erro ao deletar pet #'{pet_nome}', {error_msg}")
        return {"mesage": error_msg}, 404


@app.post('/contato', tags=[contato_tag],
          responses={"200": PetViewSchema, "404": ErrorSchema})
def add_contato(form: ContatoSchema):
    """Adiciona de um novo contato à um pet cadastrado na base identificado pelo id

    Retorna uma representação dos pets e contato associados.
    """
    pet_id  = form.pet_id
    logger.debug(f"Adicionando contatos ao pet #{pet_id}")    
    session = Session()
    pet = session.query(Pet).filter(Pet.id == pet_id).first()

    if not pet:
        error_msg = "Pet não encontrado na base :/"
        logger.warning(f"Erro ao adicionar contato ao pet '{pet_id}', {error_msg}")
        return {"mesage": error_msg}, 404

    texto = form.texto
    contato = Contato(texto)

    pet.adiciona_contato(contato)
    session.commit()

    logger.debug(f"Adicionado comentário ao pet #{pet_id}")

    return apresenta_pet(pet), 200

@app.get('/tipos-animal', tags=[tipo_animal_tag],
    responses={"200": ListagemTiposAnimalPetSchema, "404": ErrorSchema})
def get_tipos_animal():
    """Faz a busca por todos os tipos de animal

    Retorna uma representação da listagem de tipos de animal.
    """
    logger.debug(f"Coletando tipos de pet ")
    session = Session()
    tipos_animal = session.query(TipoAnimal).all()

    if not tipos_animal:
        return {"tipos": []}, 200
    else:
        logger.debug(f"%d tipos de pet encontrados" % len(tipos_animal))
        # retorna a representação de pet
        print(tipos_animal)
        return apresenta_tipos_animal(tipos_animal), 200
    

@app.get('/tipos-contato', tags=[tipo_contato_tag],
    responses={"200": ListagemTiposContatoSchema, "404": ErrorSchema})
def get_tipos_contato():
    """Faz a busca por todos os tipos de contato

    Retorna uma representação da listagem de tipos de contato.
    """
    logger.debug(f"Coletando tipos de contato ")    
    session = Session()
    tipos_contato = session.query(TipoContato).all()

    if not tipos_contato:
        return {"tipos": []}, 200
    else:
        logger.debug(f"%d tipos de contato encontrados" % len(tipos_contato))
        print(tipos_contato)
        return apresenta_tipos_contato(tipos_contato), 200
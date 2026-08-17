# Diagrama de classes

Classes de persistência do domínio. As multiplicidades — ausentes na entrega do
PIT I — estão explícitas, e as classes de domínio (`Categoria`, `Prioridade`,
`Status`) substituíram os campos de texto livre do modelo anterior.

```mermaid
classDiagram
    class Usuario {
        +int id
        +String nome
        +String email
        -String senha_hash
        +String perfil
        +String departamento
        +bool ativo
        +DateTime criado_em
        +definir_senha(senha) void
        +conferir_senha(senha) bool
        +pode_ver_chamado(chamado) bool
        +eh_gestor() bool
        +eh_tecnico() bool
    }

    class Chamado {
        +int id
        +String protocolo
        +String titulo
        +String descricao
        +DateTime data_abertura
        +DateTime data_encerramento
        +String solucao
        +prazo_sla() DateTime
        +sla_estourado() bool
        +horas_em_aberto() float
        +encerrado() bool
    }

    class Interacao {
        +int id
        +String mensagem
        +String tipo
        +DateTime criado_em
    }

    class Anexo {
        +int id
        +String nome_arquivo
        +int tamanho_bytes
        +DateTime enviado_em
    }

    class Categoria {
        +int id
        +String nome
        +String descricao
        +bool ativo
    }

    class Prioridade {
        +int id
        +String nome
        +int sla_horas
        +int ordem
    }

    class Status {
        +int id
        +String nome
        +bool encerra
        +int ordem
    }

    Usuario "1" --> "0..*" Chamado : abre (solicitante)
    Usuario "0..1" --> "0..*" Chamado : atende (tecnico)
    Usuario "1" --> "0..*" Interacao : registra
    Chamado "1" *-- "0..*" Interacao : histórico
    Chamado "1" *-- "0..*" Anexo : arquivos
    Categoria "1" --> "0..*" Chamado : classifica
    Prioridade "1" --> "0..*" Chamado : define SLA
    Status "1" --> "0..*" Chamado : estado atual
```

## Notas de modelagem

**Composição × associação.** `Interacao` e `Anexo` são composições de `Chamado`:
não existem fora dele e são removidos junto (`ON DELETE CASCADE`). Já
`Categoria`, `Prioridade` e `Status` são associações — existem
independentemente e não podem ser apagados enquanto houver chamado apontando
para eles (`ON DELETE RESTRICT`).

**Duas associações entre `Usuario` e `Chamado`.** Uma pessoa participa do
chamado em dois papéis distintos — solicitante (obrigatório) e técnico
(opcional). No banco, isso vira duas chaves estrangeiras para a mesma tabela.

**`Perfil` não virou tabela.** É um enumerado estável de três valores, validado
por `CHECK` no banco. Uma tabela aqui só acrescentaria uma junção em toda
consulta, sem ganho.

**`senha_hash` é privado.** A senha nunca é lida diretamente: entra por
`definir_senha()` e é conferida por `conferir_senha()`.

**Métodos calculados no model.** `prazo_sla`, `sla_estourado` e
`horas_em_aberto` são propriedades da própria entidade, não do serviço — são
características intrínsecas do chamado, e mantê-las juntas dos dados evita
duplicar a fórmula em cada lugar que precisa dela.

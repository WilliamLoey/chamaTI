# Escopo do projeto

## Problema

Em pequenas e médias empresas sem uma ferramenta de suporte, o pedido de ajuda
chega por e-mail, WhatsApp ou no corredor. Isso produz quatro sintomas que se
repetem:

1. **Perda de solicitações** — o pedido some na caixa de entrada de alguém.
2. **Ausência de prazo** — ninguém sabe quando algo deveria ter sido resolvido.
3. **Retrabalho** — sem histórico, o mesmo problema é diagnosticado do zero.
4. **Falta de dados** — o gestor não sabe quantos chamados existem, de que tipo
   ou quanto tempo levam.

## Público-alvo

Empresas de 20 a 200 funcionários com equipe de TI interna de 1 a 5 pessoas.

Três perfis de usuário:

| Perfil | Quem é | O que precisa |
|---|---|---|
| Solicitante | Funcionário de qualquer setor | Pedir ajuda e saber o andamento |
| Técnico | Analista de suporte | Ver a fila, priorizar e registrar o atendimento |
| Gestor | Coordenador de TI | Enxergar o todo e distribuir a carga |

## Objetivo

Centralizar o ciclo de vida do chamado — abertura, triagem, atendimento e
encerramento — em uma aplicação web, com protocolo, responsável, prazo e
histórico para cada solicitação.

## Escopo do MVP

Entra nesta entrega:

- Cadastro e autenticação com três perfis de acesso
- Abertura de chamado com categoria, prioridade, descrição e anexos
- Geração de protocolo único
- Fila de chamados com filtros (status, prioridade, período, busca textual) e paginação
- Atribuição de técnico responsável
- Fluxo de status controlado, com transições válidas definidas
- Histórico de interações com autor e data
- Encerramento com registro obrigatório da solução
- Cálculo e sinalização de SLA por prioridade
- Painel de indicadores para o gestor
- Interface responsiva

## Fora do escopo (fase 2)

Estes itens estavam no planejamento original do PIT I e foram remanejados
conscientemente, por não serem necessários para validar a hipótese central do
projeto:

| Item | Motivo do adiamento |
|---|---|
| Base de conhecimento | Depende de um volume de chamados resolvidos que ainda não existe |
| Pesquisa de satisfação (CSAT) | Faz sentido apenas depois que o fluxo estiver em uso real |
| Exportação de relatórios em PDF | O painel na tela já atende à necessidade imediata do gestor. **Pedido de novo na validação** (laudo de Juliana, perfil Gestor): é o primeiro item da fase 2 |
| Importação de usuários por CSV | Volume de usuários do piloto não justifica |
| Notificação por e-mail | Exige serviço externo e configuração de domínio |
| Aplicativo móvel nativo | A interface responsiva cobre o uso em celular |

## Hipótese a validar

> Se o solicitante tiver um canal único com protocolo e prazo visível, e o
> gestor enxergar a fila em tempo real, o tempo médio de atendimento cai e
> nenhuma solicitação se perde.

**Como medir:** tempo médio de atendimento e taxa de cumprimento de SLA, ambos
disponíveis no painel desde o primeiro dia de uso.

## Restrições

- Prazo: um semestre letivo, com desenvolvimento individual
- Custo: apenas ferramentas gratuitas ou de plano gratuito
- Hospedagem: plano gratuito do Render (o serviço hiberna após inatividade)
- O SGBD precisa ser popular e de fácil manutenção — daí a escolha do PostgreSQL

## Critérios de aceite do MVP

- [x] Um solicitante consegue abrir um chamado e receber o protocolo
- [x] Um técnico consegue assumir, comentar e resolver o chamado
- [x] Um gestor enxerga todos os chamados e os indicadores
- [x] Um solicitante não consegue ver o chamado de outro, nem pela URL direta
- [x] A listagem responde rapidamente com mais de 200 chamados na base
- [x] A aplicação é utilizável em tela de 360 px de largura
- [x] Toda regra de negócio é validada no servidor

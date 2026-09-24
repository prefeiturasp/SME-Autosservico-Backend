.. _core:

Core
======================================================================

O app ``core`` concentra autenticação (chave de API), o endpoint de
health check e utilidades compartilhadas entre os demais domínios.

Health Check
----------------------------------------------------------------------

Endpoint utilizado por probes de liveness/orquestradores para verificar
se o processo da aplicação está no ar.

.. automodule:: apps.core.api.views
   :members:
   :noindex:

.. automodule:: apps.core.api.serializers
   :members:
   :noindex:

Autenticação
----------------------------------------------------------------------

Esquema de autenticação por chave de API (header HTTP), padrão SME para
microsserviços.

.. automodule:: apps.core.authentication
   :members:
   :noindex:

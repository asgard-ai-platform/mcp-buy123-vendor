"""mcp_buy123_vendor — src-layout 套件根目錄。

此套件為 src-layout 遷移的試點起點。
Phase 2.1 僅遷移低耦合的共用模組（config.constants）。
其餘模組（connectors、app、tools、auth）將於後續階段（Phase 2.2+）逐步遷入，
屆時其相依的 config.settings 與 auth.vendor_login 亦已完成遷移。
"""

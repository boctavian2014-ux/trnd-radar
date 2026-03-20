import os
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# ca sa importam din src/comfy cand rulezi din root
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from tiktok_trends import get_tiktok_trends
from trends import render_dashboard


def _comfy_available() -> bool:
    import os
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env")
    return bool(os.getenv("COMFY_CLOUD_API_KEY"))


def _default_mirofish_url() -> str:
    return os.getenv("MIROFISH_API_URL", "http://localhost:5001")


def _perplexity_available() -> bool:
    return bool(os.getenv("PERPLEXITY_API_KEY"))


def render_perplexity_section() -> None:
    st.subheader("Auto Research - Perplexity API")
    if not _perplexity_available():
        st.info("Seteaza `PERPLEXITY_API_KEY` in `.env` (local) sau Railway Variables.")
        return

    try:
        from research.perplexity_client import PerplexityError, research_query
    except Exception as e:
        st.warning(f"Modulul Perplexity nu s-a incarcat: {e}. Verifica `src/research/`.")
        return

    with st.expander("Cauta rapid cu surse web", expanded=True):
        query = st.text_area(
            "Intrebare / task research",
            placeholder="Ex: Care sunt trendurile sociale dominante in Romania in 2026 si ce impact au pentru branduri?",
            height=100,
            key="perplexity_query",
        )
        focus = st.text_input(
            "Focus (optional)",
            placeholder="Ex: retail, fintech, creator economy",
            key="perplexity_focus",
        )
        model = st.text_input(
            "Model (optional)",
            value=os.getenv("PERPLEXITY_MODEL", "sonar"),
            key="perplexity_model",
        )

        if st.button("Ruleaza research", type="primary"):
            if not query.strip():
                st.warning("Scrie o intrebare.")
            else:
                try:
                    with st.spinner("Perplexity analizeaza..."):
                        result = research_query(query=query.strip(), focus=focus.strip(), model=model.strip())
                    st.success(f"Gata. Model: {result.get('model')}")
                    st.markdown(result.get("answer") or "_Fara raspuns text._")
                    citations = result.get("citations", [])
                    if citations:
                        st.markdown("**Surse:**")
                        for idx, url in enumerate(citations, start=1):
                            st.markdown(f"{idx}. {url}")
                except PerplexityError as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Eroare neasteptata: {exc}")


def render_comfy_section() -> None:
    if not _comfy_available():
        with st.expander("Comfy Cloud – imagine / video (necesita config)"):
            st.info(
                "1. `.env`: `COMFY_CLOUD_API_KEY=...` (de pe cloud.comfy.org)\n"
                "2. In root: `workflow_api.json` (imagine), `workflow_video_api.json` (video)\n"
                "3. Reincarca pagina."
            )
            st.caption("Detalii: COMFY.md")
        return

    try:
        from comfy.comfy_client import ComfyCloudError
        from comfy.comfy_topics import generate_topic_image, generate_topic_reel
    except Exception as e:
        st.warning(f"Modulul Comfy nu s-a incarcat: {e}. Verifica ca exista src/comfy/.")
        return

    st.subheader("Comfy Cloud – imagine / video")
    st.caption("Topic + descriere → imagine (thumbnail) sau reel. Workflow-uri: workflow_api.json, workflow_video_api.json.")
    topic_name = st.text_input("Topic", placeholder="ex: Viral Romania 2025", key="comfy_topic")
    description = st.text_area("Descriere prompt", placeholder="ex: Postere colorat, stil modern.", height=80, key="comfy_desc")

    col_img, col_vid = st.columns(2)
    with col_img:
        st.markdown("**Imagine**")
        if st.button("Genereaza imagine"):
            if not topic_name or not description.strip():
                st.warning("Completeaza topic si descriere.")
            else:
                try:
                    with st.spinner("Se trimite workflow-ul la Comfy Cloud..."):
                        workflow_path = str(_ROOT / "workflow_api.json")
                        image_path = generate_topic_image(
                            topic_name=topic_name,
                            description=description.strip(),
                            workflow_path=workflow_path,
                            output_dir=str(_ROOT / "outputs" / "topics"),
                        )
                    if image_path:
                        st.success("Gata.")
                        st.image(image_path, caption=Path(image_path).name)
                    else:
                        st.error("Niciun fisier. Verifica workflow_api.json.")
                except ComfyCloudError as exc:
                    st.error(f"Comfy Cloud: {exc}")
                except FileNotFoundError as exc:
                    st.error(f"Lipseste fisierul workflow: {exc}")
                except Exception as exc:
                    st.error(str(exc))

    with col_vid:
        st.markdown("**Video / Reel**")
        video_workflow_exists = (_ROOT / "workflow_video_api.json").is_file() or (_ROOT / "workflow_video_api.json.json").is_file()
        if not video_workflow_exists:
            st.info("**Pentru reel:** pune în root fișierul **workflow_video_api.json** (sau workflow_video_api.json.json). Exportă workflow-ul video din Comfy UI → format API → salvează în folderul proiectului.")
        with st.expander("Avansat: Node ID / Input (workflow video)"):
            video_node_id = st.text_input("Node ID prompt (ex: 2 sau 6)", "6", key="comfy_video_node")
            video_input_key = st.text_input("Input key (ex: text)", "text", key="comfy_video_input")
            st.caption("In JSON-ul workflow-ului, gasesti node-ul de prompt (ex. CLIPTextEncode) si ID-ul lui; input-ul e de obicei \"text\".")
        if st.button("Genereaza reel"):
            if not topic_name or not description.strip():
                st.warning("Completeaza topic si descriere.")
            else:
                try:
                    with st.spinner("Video in curs (poate dura minute)..."):
                        workflow_path = str(_ROOT / "workflow_video_api.json")
                        video_path = generate_topic_reel(
                            topic_name=topic_name,
                            description=description.strip(),
                            workflow_path=workflow_path,
                            text_node_id=video_node_id.strip() or "6",
                            text_input_name=video_input_key.strip() or "text",
                            output_dir=str(_ROOT / "outputs" / "reels"),
                        )
                    if video_path:
                        st.success("Gata.")
                        st.video(video_path)
                        st.caption(Path(video_path).name)
                    else:
                        st.error("Niciun video. Verifica workflow_video_api.json.")
                except ComfyCloudError as exc:
                    st.error(f"Comfy Cloud: {exc}")
                except FileNotFoundError:
                    st.error(
                        "Lipsește fișierul workflow video. Pune în folderul proiectului (root) fișierul **workflow_video_api.json** "
                        "(sau workflow_video_api.json.json). Exportă din Comfy UI → Save/Export → format API."
                    )
                except Exception as exc:
                    st.error(str(exc))


def render_tiktok_section() -> None:
    st.subheader("TikTok – trenduri virale")
    st.caption("Regiune + nr. clipuri → Apify. Apasa butonul pentru a incarca.")
    col_filters, _ = st.columns([2, 1])
    with col_filters:
        region = st.selectbox(
            "Regiune",
            options=["RO", "US", "GB", "DE"],
            index=0,
            help="Tara/regiunea pentru care se cauta clipuri populare.",
        )
        limit = st.slider("Numar clipuri", min_value=5, max_value=50, value=10, help="Cate rezultate sa fie afisate.")
    if st.button("Incarca trenduri TikTok", type="primary"):
        with st.spinner("Se incarca datele TikTok..."):
            try:
                data = get_tiktok_trends(limit=limit, region=region)
                if data:
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.success(f"Afisate {len(df)} clipuri pentru regiunea **{region}**.")
                else:
                    st.info("Nu au fost gasite rezultate pentru filtrul ales. Incearca alta regiune sau mai multe clipuri.")
            except Exception as exc:
                st.error(f"Eroare la incarcarea trendurilor TikTok: {exc}")


def render_mirofish_section() -> None:
    st.subheader("MiroFish – swarm intelligence / predicții")
    st.caption(
        "Funcțiile MiroFish (graf, simulare, raport) sunt apelate direct din acest dashboard prin API. "
        "Backend-ul MiroFish trebuie să ruleze (npm run dev în folderul MiroFish). Tot textul de aici e în română."
    )

    with st.expander("Cum funcționează și ce trebuie să încarci (pas cu pas)"):
        st.markdown("""
**Ce e MiroFish aici:** un motor care ia **documente** (PDF/MD/TXT) și o **cerință de simulare** (ce vrei să „prezici”), construiește un graf de entități, apoi rulează o simulare pe Twitter + Reddit cu agenți virtuali și generează un raport.

**Pas 1 – Ce încarci:**
- **Fișiere:** cel puțin un document în **PDF**, **MD** sau **TXT**. Exemple: un raport de știri, un articol, un text despre un subiect (eveniment, persoană, organizație). Acestea sunt „semințele” din care MiroFish extrage entități (persoane, organizații, concepte) și relații.
- **Cerința de simulare:** un text în limbaj natural care spune **ce vrei să simulezi**. Exemple:
  - *„Dacă compania X anunță concedieri masive, cum reacționează utilizatorii pe Twitter și Reddit?”*
  - *„Cum se răspândește o știre despre evenimentul Y în primele 24 de ore?”*
  - *„Ce sentiment au utilizatorii față de măsura Z?”*
- **Nume proiect:** un nume pentru acest proiect (ex. „Test 1” sau „Simulare știri”).

**Cum mergi mai departe:** după ce apeși **„Generează ontologie și creează proiect”**, MiroFish analizează documentele și cerința și creează un proiect. Apoi parcurgi **Pașii 2–6** în ordine: construiești graful (2), creezi simularea (3), o pregătești (4), o pornești (5) și la final generezi raportul (6). Fiecare pas are un buton dedicat; unele durează câteva minute.
        """)
        st.caption("Detalii complete: fișierul MIROFISH-PAS-CU-PAS.md din folderul proiectului.")

    try:
        from mirofish.mirofish_client import (
            MiroFishError,
            check_health,
            ontology_generate,
            graph_build,
            graph_task_status,
            wait_graph_build,
            simulation_create,
            simulation_prepare,
            simulation_prepare_status,
            simulation_start,
            report_generate,
            report_generate_status,
            report_by_simulation,
            project_list,
            simulation_list,
        )
    except Exception as e:
        st.warning(f"Modulul MiroFish nu s-a încărcat: {e}. Verifică că există src/mirofish/.")
        return

    base_url = st.text_input(
        "URL API MiroFish",
        value=st.session_state.get("mirofish_base_url", _default_mirofish_url()),
        key="mirofish_url",
        help="Backend MiroFish (ex. http://localhost:5001). În terminal: cd C:\\Users\\octav\\Desktop\\MiroFish apoi npm run dev.",
    )
    st.session_state["mirofish_base_url"] = base_url

    if not base_url.strip():
        st.info("Introdu URL-ul API MiroFish (ex. http://localhost:5001) și asigură-te că backend-ul rulează.")
        return

    try:
        ok = check_health(base_url.strip())
    except Exception as e:
        st.error(f"MiroFish nu răspunde la {base_url}: {e}")
        return
    if not ok:
        st.warning(f"Backend-ul MiroFish nu răspunde la {base_url}. Pornește-l cu `npm run dev` în folderul MiroFish.")
        return
    st.success("MiroFish backend este pornit.")

    # Session state pentru flow
    if "mirofish_project_id" not in st.session_state:
        st.session_state["mirofish_project_id"] = None
    if "mirofish_simulation_id" not in st.session_state:
        st.session_state["mirofish_simulation_id"] = None

    # --- Pas 1: Încarcă documente + cerință simulare ---
    with st.expander("Pas 1: Încarcă documente și cerința de simulare", expanded=True):
        uploads = st.file_uploader(
            "Fișiere (PDF, MD, TXT) – cel puțin unul",
            type=["pdf", "md", "txt"],
            accept_multiple_files=True,
            key="mirofish_uploads",
        )
        scenario = st.selectbox(
            "Scenariu (opțional – completează cerința mai jos)",
            ["— Alege unul sau scrie manual —", "Viralitate app: cât de virală poate deveni aplicația"],
            key="mirofish_scenario",
        )
        default_requirement = (
            "Cât de virală poate deveni această aplicație pe Twitter și Reddit în primele săptămâni? "
            "Simulează reacțiile utilizatorilor, partajările și discuțiile."
            if scenario == "Viralitate app: cât de virală poate deveni aplicația"
            else ""
        )
        sim_requirement = st.text_area(
            "Cerința de simulare / predicție (în limbaj natural)",
            value=default_requirement,
            placeholder="Ex: Dacă X anunță Y, cum reacționează opinia publică? Sau: Cât de virală poate deveni această app pe Twitter și Reddit?",
            height=100,
            key="mirofish_requirement",
        )
        uploads_count = len(uploads) if uploads else 0
        requirement_len = len(sim_requirement.strip()) if sim_requirement else 0
        st.caption(f"Verificare input: fișiere selectate = {uploads_count}, lungime cerință = {requirement_len} caractere")
        if scenario == "Viralitate app: cât de virală poate deveni aplicația":
            st.caption("Încarcă un fișier MD/PDF/TXT cu descrierea app-ului (ce face, pentru cine, de ce ar putea fi virală). Detalii: MIROFISH-PAS-CU-PAS.md → „Măsurarea viralității unei aplicații”.")
        project_name = st.text_input("Nume proiect", value="Proiect Dashboard", key="mirofish_project_name")
        can_submit = uploads_count > 0 and requirement_len > 0
        if st.button("Generează ontologie și creează proiect", disabled=not can_submit):
            if not uploads or not sim_requirement.strip():
                st.warning("Încarcă cel puțin un fișier și completează cerința de simulare.")
            else:
                try:
                    files = [(f.name, f.getvalue()) for f in uploads]
                    data = ontology_generate(
                        base_url.strip(),
                        files,
                        simulation_requirement=sim_requirement.strip(),
                        project_name=project_name.strip() or "Proiect Dashboard",
                    )
                    st.session_state["mirofish_project_id"] = data["project_id"]
                    st.success(f"Proiect creat: **{data['project_id']}**. Poți trece la Pas 2.")
                    st.json({"project_id": data["project_id"], "entity_types": len(data.get("ontology", {}).get("entity_types", []))})
                except MiroFishError as e:
                    st.error(str(e))

    project_id = st.session_state.get("mirofish_project_id")
    if not project_id:
        st.caption("După ce creezi un proiect (Pas 1), aici vor apărea pașii 2–6.")
        return

    st.write("---")
    st.caption(f"Proiect activ: **{project_id}**")

    # --- Pas 2: Construiește graf ---
    with st.expander("Pas 2: Construiește graful (GraphRAG)"):
        if st.button("Pornește construcția grafului"):
            try:
                data = graph_build(base_url.strip(), project_id)
                task_id = data.get("task_id")
                if not task_id:
                    st.error("API nu a returnat task_id.")
                else:
                    with st.spinner("Se construiește graful (poate dura minute)..."):
                        wait_graph_build(base_url.strip(), task_id)
                    st.success("Graf construit. Poți trece la Pas 3.")
                    st.rerun()
            except MiroFishError as e:
                st.error(str(e))

    # --- Pas 3: Creează simulare ---
    with st.expander("Pas 3: Creează simularea"):
        if st.button("Creează simulare (Twitter + Reddit)"):
            try:
                data = simulation_create(base_url.strip(), project_id)
                st.session_state["mirofish_simulation_id"] = data["simulation_id"]
                st.success(f"Simulare creată: **{data['simulation_id']}**. Poți trece la Pas 4.")
                st.rerun()
            except MiroFishError as e:
                st.error(str(e))

    sim_id = st.session_state.get("mirofish_simulation_id")
    if not sim_id:
        st.caption("După Pas 3 (creează simulare) vor apărea Pașii 4–6.")
        return

    # --- Pas 4: Pregătește simularea ---
    with st.expander("Pas 4: Pregătește simularea (agenți, config)"):
        if st.button("Pregătește simularea"):
            try:
                data = simulation_prepare(base_url.strip(), sim_id)
                task_id = data.get("task_id")
                if task_id:
                    with st.spinner("Pregătire în curs (poate dura minute)..."):
                        for _ in range(300):
                            time.sleep(2)
                            r = simulation_prepare_status(base_url.strip(), {"task_id": task_id, "simulation_id": sim_id})
                            d = r.get("data", r) if isinstance(r, dict) else {}
                            status = d.get("status", "")
                            if status == "ready" or d.get("already_prepared"):
                                break
                            if status in ("failed", "error"):
                                st.error(d.get("message", str(d)))
                                break
                        else:
                            st.warning("Timeout. Verifică în MiroFish dacă pregătirea s-a terminat.")
                    st.success("Pregătire completă. Poți trece la Pas 5.")
                else:
                    st.info("Pregătire deja făcută sau a eșuat. Verifică backend.")
                st.rerun()
            except MiroFishError as e:
                st.error(str(e))
            except Exception as e:
                st.error(str(e))

    # --- Pas 5: Pornește simularea ---
    with st.expander("Pas 5: Pornește rularea simulării"):
        max_rounds = st.number_input("Număr maxim runde (opțional)", min_value=0, value=0, help="0 = implicit")
        if st.button("Pornește simularea"):
            try:
                data = simulation_start(
                    base_url.strip(),
                    sim_id,
                    max_rounds=max_rounds if max_rounds else None,
                )
                st.success("Simularea rulează. Poți verifica statusul în MiroFish sau aștepta și genera raport (Pas 6).")
            except MiroFishError as e:
                st.error(str(e))

    # --- Pas 6: Generează raport ---
    with st.expander("Pas 6: Generează raport"):
        if st.button("Generează raport"):
            try:
                data = report_generate(base_url.strip(), sim_id)
                task_id = data.get("task_id")
                if task_id:
                    with st.spinner("Se generează raportul..."):
                        for _ in range(120):
                            time.sleep(2)
                            r = report_generate_status(base_url.strip(), {"task_id": task_id, "simulation_id": sim_id})
                            d = r.get("data", r) if isinstance(r, dict) else {}
                            status = d.get("status", "")
                            if status == "completed" or d.get("already_completed"):
                                break
                            if status == "failed":
                                st.error(d.get("message", str(d)))
                                break
                    report = report_by_simulation(base_url.strip(), sim_id)
                    if report:
                        st.success(f"Raport generat: **{report.get('report_id', '')}**. Detalii în MiroFish.")
                        st.json({"report_id": report.get("report_id"), "status": report.get("status")})
                    else:
                        st.info("Raport în curs sau verifică în MiroFish.")
                else:
                    st.info("Raport deja existent sau a eșuat. Verifică backend.")
            except MiroFishError as e:
                st.error(str(e))
            except Exception as e:
                st.error(str(e))

    st.caption("Toate acțiunile sunt în română. Backend-ul MiroFish poate returna mesaje în chineză în log-uri; pentru detalii deschide http://localhost:3000.")


if __name__ == "__main__":
    render_dashboard()
    st.divider()
    render_perplexity_section()
    st.divider()
    render_tiktok_section()
    st.divider()
    render_comfy_section()
    st.divider()
    render_mirofish_section()

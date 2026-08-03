// Datos comprobados del clip determinista de descubrimiento y cribado.
// La consulta se ejecutó una vez en Semantic Scholar; el clip no vuelve a
// buscar, no ordena resultados y no llama a una API durante la clase.

window.CLIP_DATA = {
  meta: {
    titulo: "Descubrimiento y cribado",
    pregunta:
      "Entre adultos, ¿los mensajes o diálogos persuasivos generados o mediados por LLM cambian actitudes, creencias, intenciones o conducta?",
    contexto:
      "Muestra didáctica del corpus de IA y persuasión · no es una revisión exhaustiva",
    consulta:
      '"large language model" persuasion human attitudes beliefs intentions behavior',
    fuente: "Semantic Scholar · búsqueda por relevancia",
    fechaConsulta: "2026-08-02",
    resultadosTotales: 452,
    consultaEjecutada: true,
    verificadoEl: "2026-08-02",
  },

  criterios: [
    {
      clave: "C1",
      nombre: "Población",
      texto: "Personas adultas expuestas al tratamiento, no solo modelos o jueces de texto",
    },
    {
      clave: "C2",
      nombre: "Intervención",
      texto: "Mensaje o diálogo persuasivo generado o mediado por un LLM",
    },
    {
      clave: "C3",
      nombre: "Resultado",
      texto: "Comparación pertinente y actitud, creencia, intención o conducta medida después",
    },
  ],

  ambito: "2023–2026 · estudio empírico primario · estado editorial registrado",

  registros: [
    {
      id: "r1",
      autores: "Matz y coautores",
      anio: 2024,
      corto: "Personalized persuasion at scale",
      titulo: "The potential of generative AI for personalized persuasion at scale",
      venue: "Scientific Reports",
      doi: "10.1038/s41598-024-53755-0",
      verificado: true,
    },
    {
      id: "r2",
      autores: "Hackenburg y Margetts",
      anio: 2024,
      corto: "Political microtargeting with LLMs",
      titulo: "Evaluating the persuasive influence of political microtargeting with large language models",
      venue: "PNAS",
      doi: "10.1073/pnas.2403116121",
      verificado: true,
    },
    {
      id: "r3",
      autores: "Salvi y coautores",
      anio: 2025,
      corto: "Conversational persuasiveness of GPT-4",
      titulo: "On the conversational persuasiveness of GPT-4",
      venue: "Nature Human Behaviour",
      doi: "10.1038/s41562-025-02194-6",
      verificado: true,
    },
    {
      id: "r4",
      autores: "Bai y coautores",
      anio: 2025,
      corto: "Messages can persuade on policy issues",
      titulo: "LLM-generated messages can persuade humans on policy issues",
      venue: "Nature Communications",
      doi: "10.1038/s41467-025-61345-5",
      verificado: true,
    },
    {
      id: "r5",
      autores: "Hackenburg y coautores",
      anio: 2025,
      corto: "Levers of political persuasion",
      titulo: "The levers of political persuasion with conversational artificial intelligence",
      venue: "Science",
      doi: "10.1126/science.aea3884",
      verificado: true,
    },
    {
      id: "r6",
      autores: "Costello, Pennycook y Rand",
      anio: 2024,
      corto: "Reducing conspiracy beliefs",
      titulo: "Durably reducing conspiracy beliefs through dialogues with AI",
      venue: "Science · expresión editorial de preocupación (2026)",
      doi: "10.1126/science.adq1814",
      verificado: true,
    },
    {
      id: "r7",
      autores: "Breum y coautores",
      anio: 2024,
      corto: "Persuasive power of LLMs",
      titulo: "The Persuasive Power of Large Language Models",
      venue: "ICWSM",
      doi: "10.1609/icwsm.v18i1.31304",
      verificado: true,
    },
    {
      id: "r8",
      autores: "Li y Yang",
      anio: 2024,
      corto: "AI-generated content labels",
      titulo: "Impact of Artificial Intelligence–Generated Content Labels On Perceived Accuracy, Message Credibility, and Sharing Intentions for Misinformation: Web-Based, Randomized, Controlled Experiment",
      venue: "JMIR Formative Research",
      doi: "10.2196/60024",
      verificado: true,
    },
  ],

  // Tres decisiones visibles: incluir, excluir y separar por estado editorial.
  decisiones: [
    {
      registro: "r4",
      veredicto: "Incluir",
      marcas: [
        { clave: "C1", valor: "si", nota: "Participantes humanos adultos" },
        { clave: "C2", valor: "si", nota: "Mensajes generados por LLM" },
        {
          clave: "C3",
          valor: "si",
          nota: "Comparadores y apoyo a políticas después del mensaje",
          decisivo: true,
        },
      ],
      nota:
        "Tres experimentos preregistrados: coincide la población, la intervención, el comparador y el resultado.",
    },
    {
      registro: "r7",
      veredicto: "Excluir",
      marcas: [
        {
          clave: "C1",
          valor: "no",
          nota: "La persuasión ocurre entre modelos; humanos juzgan argumentos",
          decisivo: true,
        },
        { clave: "C2", valor: "si", nota: "Los argumentos sí los genera un LLM" },
        { clave: "C3", valor: "no", nota: "No mide cambio humano tras exposición" },
      ],
      nota:
        "Las palabras clave coinciden, pero el diseño no responde nuestra pregunta. Es evidencia para otro corpus.",
    },
    {
      registro: "r6",
      veredicto: "Bandera: no sintetizar",
      marcas: [
        { clave: "C1", valor: "si", nota: "Adultos con creencias conspirativas" },
        { clave: "C2", valor: "si", nota: "Diálogos personalizados con GPT-4 Turbo" },
        {
          clave: "C3",
          valor: "?",
          nota: "Cumple alcance; estado editorial abierto desde 2026",
          decisivo: true,
        },
      ],
      nota:
        "Science publicó una Editorial Expression of Concern (doi 10.1126/science.aej2383). El registro queda separado hasta resolución.",
    },
  ],

  resultado: {
    filas: [
      { etiqueta: "Incluidos para extracción", valor: 5 },
      { etiqueta: "Excluidos con razón", valor: 2 },
      { etiqueta: "Bandera editorial", valor: 1 },
      { etiqueta: "Decisiones sin motivo escrito", valor: 0 },
    ],
    lead: "La salida es un corpus con decisiones y razones, no un resumen.",
  },

  limites: [
    "Una consulta, una plataforma y un día: no es una búsqueda exhaustiva",
    "Los ocho candidatos fueron curados; no son los ocho primeros resultados",
    "Aquí se verificó metadato y alcance; no se evaluó calidad metodológica completa",
    "Una advertencia editorial cambia el estado del registro, no se oculta",
  ],

  cierre: {
    lead:
      "El cribado se puede acelerar. La decisión de qué cuenta como evidencia, no.",
    puente:
      "Ahora ustedes: una extracción tentativa y una afirmación verificada por pareja.",
  },

  pasos: [
    { vista: "pregunta", dur: 14, capitulo: "Pregunta" },
    { vista: "criterios", dur: 18, capitulo: "Criterios" },
    { vista: "consulta", dur: 16, capitulo: "Consulta" },
    { vista: "candidatos", revelar: 1, dur: 2.5, capitulo: "Candidatos" },
    { vista: "candidatos", revelar: 2, dur: 2.5 },
    { vista: "candidatos", revelar: 3, dur: 2.5 },
    { vista: "candidatos", revelar: 4, dur: 2.5 },
    { vista: "candidatos", revelar: 5, dur: 2.5 },
    { vista: "candidatos", revelar: 6, dur: 2.5 },
    { vista: "candidatos", revelar: 7, dur: 2.5 },
    { vista: "candidatos", revelar: 8, dur: 2.5 },
    { vista: "decision", indice: 0, dur: 22, capitulo: "Cribado" },
    { vista: "decision", indice: 1, dur: 18 },
    { vista: "decision", indice: 2, dur: 24 },
    { vista: "resultado", dur: 18, capitulo: "Cierre" },
    { vista: "limites", dur: 16 },
    { vista: "cierre", dur: 14 },
  ],
};

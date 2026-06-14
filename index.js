const pptxgen = require('pptxgenjs');

// Create presentation
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_16x9';
pptx.title = 'Sistema de Monitoramento de EPIs - Facchini';

// Define Colors
const COLORS = {
  NAVY: '0C2340',      // Deep Corporate Navy (Facchini primary feel)
  BLUE: '005EA6',      // Brand Blue
  ORANGE: 'E25822',    // Safety / Warning Orange (Accent)
  LIGHT_BG: 'F8FAFC',  // Sleek off-white/light gray background
  CARD_BG: 'FFFFFF',   // Pure White for cards
  TEXT_MAIN: '1E293B', // Slate 800
  TEXT_MUTED: '64748B',// Slate 500
  WHITE: 'FFFFFF',
  BORDER: 'E2E8F0',    // Slate 200
  GREEN: '10B981',     // Success green
  RED: 'EF4444',       // Danger red
  LIGHT_BLUE: 'F0F7FF',// Light ice blue for container background
};

// Helper: Set Slide Background
function setBackground(slide, isDark = false) {
  slide.background = { color: isDark ? COLORS.NAVY : COLORS.LIGHT_BG };
}

// Helper: Add Standard Header to Slide
function addHeader(slide, title, subtitle = '') {
  // Top thin accent bar
  slide.addShape(pptx.shapes.RECTANGLE, {
    x: 0.5,
    y: 0.4,
    w: 12.33,
    h: 0.05,
    fill: { color: COLORS.ORANGE }
  });

  // Slide Category / Subtitle (small uppercase text)
  if (subtitle) {
    slide.addText(subtitle.toUpperCase(), {
      x: 0.5,
      y: 0.5,
      w: 10,
      h: 0.3,
      fontSize: 10,
      fontFace: 'Arial',
      bold: true,
      color: COLORS.ORANGE,
    });
  }

  // Slide Title
  slide.addText(title, {
    x: 0.5,
    y: 0.7,
    w: 11,
    h: 0.6,
    fontSize: 28,
    fontFace: 'Arial',
    bold: true,
    color: COLORS.NAVY,
  });
}

// Helper: Draw a premium Card/Box
function addCard(slide, opt) {
  const {
    x, y, w, h,
    title = '',
    body = [],
    bg = COLORS.CARD_BG,
    border = COLORS.BORDER,
    titleColor = COLORS.NAVY,
    titleSize = 16,
    bodyColor = COLORS.TEXT_MAIN,
    bodySize = 13,
    icon = null, // Can support text indicator or bullet points
    accentLine = false, // Orange accent left border
  } = opt;

  // Main Card Body
  slide.addShape(pptx.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: bg },
    line: border ? { color: border, width: 1 } : undefined,
  });

  // Left accent line if requested
  if (accentLine) {
    slide.addShape(pptx.shapes.RECTANGLE, {
      x, y,
      w: 0.06,
      h: h,
      fill: { color: COLORS.ORANGE }
    });
  }

  let textY = y + 0.2;

  // Title
  if (title) {
    slide.addText(title, {
      x: x + 0.2,
      y: textY,
      w: w - 0.4,
      h: 0.35,
      fontSize: titleSize,
      fontFace: 'Arial',
      bold: true,
      color: titleColor,
    });
    textY += 0.4;
  }

  // Body paragraphs / Bullet points
  if (body && body.length > 0) {
    body.forEach((para, idx) => {
      let isBullet = typeof para === 'string' ? false : para.bullet;
      let text = typeof para === 'string' ? para : para.text;
      let isBold = para.bold || false;
      let customColor = para.color || bodyColor;

      slide.addText(text, {
        x: x + 0.2 + (isBullet ? 0.15 : 0),
        y: textY,
        w: w - 0.4 - (isBullet ? 0.15 : 0),
        h: para.height || 0.25,
        fontSize: para.fontSize || bodySize,
        fontFace: 'Arial',
        color: customColor,
        bullet: isBullet ? { type: 'number', numberType: 'circle', code: '25FC' } : undefined,
        bold: isBold,
      });
      textY += para.height || 0.28;
    });
  }
}

// ==========================================
// SLIDE 1: Capa (Dark Navy Theme)
// ==========================================
const slide1 = pptx.addSlide();
setBackground(slide1, true);

// Decorative geometric elements
slide1.addShape(pptx.shapes.RECTANGLE, {
  x: 0,
  y: 0,
  w: 0.3,
  h: 7.5,
  fill: { color: COLORS.ORANGE }
});

slide1.addShape(pptx.shapes.RECTANGLE, {
  x: 9,
  y: 0,
  w: 4.33,
  h: 7.5,
  fill: { color: '112E52' } // Slightly lighter navy for depth
});

// Title
slide1.addText('SISTEMA INTELIGENTE DE\nMONITORAMENTO DE EPIs', {
  x: 1.0,
  y: 2.2,
  w: 8.0,
  h: 1.6,
  fontSize: 38,
  fontFace: 'Arial',
  bold: true,
  color: COLORS.WHITE,
});

// Subtitle
slide1.addText('Segurança, Controle e Eficiência Operacional para a Facchini', {
  x: 1.0,
  y: 4.0,
  w: 8.0,
  h: 0.6,
  fontSize: 18,
  fontFace: 'Arial',
  color: COLORS.ORANGE,
  bold: true,
});

// Horizontal Line divider
slide1.addShape(pptx.shapes.RECTANGLE, {
  x: 1.0,
  y: 4.8,
  w: 3.0,
  h: 0.03,
  fill: { color: COLORS.WHITE }
});

// Project metadata
slide1.addText('Proposta Técnica e Comercial\nJunho, 2026', {
  x: 1.0,
  y: 5.2,
  w: 5.0,
  h: 0.8,
  fontSize: 13,
  fontFace: 'Arial',
  color: COLORS.WHITE,
});

// ==========================================
// SLIDE 2: Contexto
// ==========================================
const slide2 = pptx.addSlide();
setBackground(slide2);
addHeader(slide2, 'A Segurança do Trabalho em Larga Escala', 'Contexto Industrial');

// Left Column: Big Statement
slide2.addText('Facchini: Referência em Implementos Rodoviários', {
  x: 0.5,
  y: 1.8,
  w: 5.5,
  h: 0.5,
  fontSize: 20,
  fontFace: 'Arial',
  bold: true,
  color: COLORS.BLUE,
});

slide2.addText(
  'Com diversos setores operacionais altamente complexos (soldagem, pintura, montagem, usinagem), a Facchini conta com milhares de colaboradores expostos diariamente a riscos ocupacionais variados.\n\n' +
  'Garantir a integridade física de cada operador não é apenas uma obrigação legal, mas um pilar estratégico de produtividade, qualidade e sustentabilidade corporativa.',
  {
    x: 0.5,
    y: 2.4,
    w: 5.5,
    h: 3.5,
    fontSize: 15,
    fontFace: 'Arial',
    color: COLORS.TEXT_MAIN,
    lineSpacing: 22,
  }
);

// Right Column: Two distinct key focus cards
addCard(slide2, {
  x: 6.8, y: 1.8, w: 5.7, h: 2.2,
  accentLine: true,
  title: 'O Desafio do Controle',
  body: [
    { text: 'Gerenciar centenas de entregas de EPIs diariamente de forma manual expõe a empresa a gargalos operacionais e erros.', bold: false },
    { text: 'Manter a conformidade legal exige rastreabilidade absoluta.', bold: true, color: COLORS.BLUE }
  ]
});

addCard(slide2, {
  x: 6.8, y: 4.4, w: 5.7, h: 2.2,
  accentLine: true,
  title: 'Objetivo Estratégico',
  body: [
    { text: 'Substituir controles reativos por monitoramento proativo e digitalizado.', bold: false },
    { text: 'Garantir que o EPI correto esteja no colaborador certo, no momento certo.', bold: true, color: COLORS.ORANGE }
  ]
});

// ==========================================
// SLIDE 3: O Problema
// ==========================================
const slide3 = pptx.addSlide();
setBackground(slide3);
addHeader(slide3, 'Os Gargalos da Gestão Manual de EPIs', 'O Problema');

// We will use 4 grid cards to show the specific problems
const problems = [
  {
    title: 'Dificuldade de Rastreabilidade',
    desc: 'Impossibilidade de auditar em segundos o histórico de entregas, trocas e vida útil de equipamentos por colaborador.'
  },
  {
    title: 'Burocracia em Auditorias',
    desc: 'Processo lento e exaustivo para coletar assinaturas e comprovar conformidade legal perante o Ministério do Trabalho.'
  }
];

problems.forEach((p, idx) => {
  const col = idx % 2;
  const row = Math.floor(idx / 2);
  const x = 0.5 + col * 6.1;
  const y = 1.8 + row * 2.6;

  addCard(slide3, {
    x, y, w: 5.7, h: 2.2,
    border: COLORS.RED, // Alert/problem colored border
    title: `${idx + 1}. ${p.title}`,
    titleColor: COLORS.RED,
    body: [
      { text: p.desc, color: COLORS.TEXT_MAIN }
    ]
  });
});

// ==========================================
// SLIDE 4: Impactos do Problema
// ==========================================
const slide4 = pptx.addSlide();
setBackground(slide4);
addHeader(slide4, 'O Custo Invisível da Ineficiência na Gestão de EPIs', 'Impactos Negativos');

// Let's create a horizontal layout of 4 columns, each showing a metric or specific impact
const impacts = [
  {
    title: 'Riscos de Acidentes',
    desc: 'Atraso na troca de EPIs vencidos ou desgastados expõe diretamente os trabalhadores a acidentes graves.',
    accent: COLORS.RED
  },
  {
    title: 'Multas e Passivos',
    desc: 'A falta de registros robustos e assinaturas digitais gera passivos trabalhistas severos e autuações legais.',
    accent: COLORS.RED
  },
  {
    title: 'Baixa Eficiência',
    desc: 'Tempo precioso de líderes de equipe e do SESMT consumido por burocracias e conferências manuais.',
    accent: COLORS.RED
  }
];

impacts.forEach((imp, idx) => {
  const x = 0.5 + idx * 4.0;
  addCard(slide4, {
    x, y: 1.8, w: 3.5, h: 4.8,
    accentLine: true,
    title: imp.title,
    titleColor: COLORS.NAVY,
    body: [
      { text: imp.desc, fontSize: 12, height: 0.22 }
    ]
  });
});

// ==========================================
// SLIDE 5: Nossa Solução
// ==========================================
const slide5 = pptx.addSlide();
setBackground(slide5);
addHeader(slide5, 'Plataforma Inteligente de Monitoramento de EPIs', 'Nossa Solução');

// Highlight banner
slide5.addShape(pptx.shapes.RECTANGLE, {
  x: 0.5, y: 1.7, w: 12.33, h: 1.2,
  fill: { color: COLORS.LIGHT_BLUE },
  line: { color: COLORS.BLUE, width: 1 }
});

slide5.addText('Uma solução de ponta a ponta desenvolvida para centralizar, automatizar e blindar a gestão de segurança na Facchini.', {
  x: 0.8, y: 1.9, w: 11.7, h: 0.8,
  fontSize: 18,
  fontFace: 'Arial',
  bold: true,
  color: COLORS.BLUE,
});

// 3 pillars
const pillars = [
  {
    title: 'Centralização Absoluta',
    desc: 'Unifica todos os setores e registros em um único dashboard acessível em tempo real.'
  },
  {
    title: 'Automação e Alertas',
    desc: 'Controles digitais impedem a entrega incorreta de EPIs e alertam automaticamente prazos de vencimento.'
  },
  {
    title: 'Rastreabilidade Total',
    desc: 'Registro eletrônico seguro e histórico imutável de todas as movimentações, entregas e devoluções.'
  }
];

pillars.forEach((p, idx) => {
  const x = 0.5 + idx * 4.2;
  addCard(slide5, {
    x, y: 3.1, w: 3.93, h: 3.5,
    accentLine: true,
    title: p.title,
    body: [
      { text: p.desc, fontSize: 13 }
    ]
  });
});

// ==========================================
// SLIDE 6: Principais Funcionalidades
// ==========================================
const slide6 = pptx.addSlide();
setBackground(slide6);
addHeader(slide6, 'Recursos Desenhados para a Dinâmica Industrial', 'Funcionalidades');

// Grid of 6 smaller functional blocks
const funcs = [
  { title: 'Gestão de Colaboradores', desc: 'Associação rápida de cargos a perfis de risco e EPIs obrigatórios.' },
  { title: 'Registro de Entregas', desc: 'Assinatura eletrônica, digital ou via crachá RFID integrado.' },
  { title: 'Histórico & Auditoria', desc: 'Rastreamento completo das movimentações com exportação em um clique.' },
  { title: 'Alertas Inteligentes', desc: 'Notificações automáticas para prazos de validade e substituições necessárias.' },
  { title: 'Business Intelligence', desc: 'Relatórios gerenciais consolidados para otimização de conformidade e consumos.' }
];

funcs.forEach((f, idx) => {
  const col = idx % 3;
  const row = Math.floor(idx / 3);
  const x = 0.5 + col * 4.2;
  const y = 1.8 + row * 2.5;

  addCard(slide6, {
    x, y, w: 3.93, h: 2.2,
    title: f.title,
    titleSize: 14,
    body: [
      { text: f.desc, fontSize: 11.5 }
    ]
  });
});

// ==========================================
// SLIDE 7: Inovação do Projeto
// ==========================================
const slide7 = pptx.addSlide();
setBackground(slide7);
addHeader(slide7, 'Tecnologia Aplicada à Prevenção', 'Inovação & Tecnologia');

// Let's create an elegant visual flow (steps from left to right)
const innovations = [
  { title: 'Processo 100% Digital', desc: 'Eliminação completa de arquivos físicos e fichas assinadas a caneta.' },
  { title: 'Validação em Tempo Real', desc: 'Inteligência de sistema que impede a entrega de EPIs incompatíveis com o cargo.' },
  { title: 'Decisões por Dados', desc: 'Analytics avançado que identifica setores com maior desgaste ou desvios de uso.' }
];

innovations.forEach((inn, idx) => {
  const x = 0.5 + idx * 4.2;
  // Step header number
  slide7.addText(`0${idx + 1}`, {
    x, y: 1.8, w: 3.93, h: 0.6,
    fontSize: 32,
    fontFace: 'Arial',
    bold: true,
    color: COLORS.ORANGE
  });

  addCard(slide7, {
    x, y: 2.5, w: 3.93, h: 4.1,
    title: inn.title,
    body: [
      { text: inn.desc, fontSize: 13, height: 0.25 }
    ]
  });
});

// ==========================================
// SLIDE 8: Benefícios para a Facchini
// ==========================================
const slide8 = pptx.addSlide();
setBackground(slide8);
addHeader(slide8, 'Valor Mensurável em Quatro Pilares', 'Retorno de Investimento');

const benefits = [
  {
    cat: 'Segurança',
    title: 'Cultura de Prevenção',
    desc: 'Redução drástica no risco de acidentes e garantia de uso constante dos EPIs corretos.',
    color: COLORS.GREEN
  },
  {
    cat: 'Gestão',
    title: 'Eficiência SESMT/RH',
    desc: 'Automação que libera a equipe de segurança para atividades de prevenção e campo.',
    color: COLORS.BLUE
  },
  {
    cat: 'Conformidade',
    title: 'Segurança Jurídica',
    desc: 'Histórico robusto de conformidade pronto para auditorias e fiscalizações a qualquer momento.',
    color: COLORS.NAVY
  }
];

benefits.forEach((b, idx) => {
  const x = 0.5 + idx * 3.9;
  const y = 1.8;

  addCard(slide8, {
    x, y, w: 3.5, h: 2.2,
    border: b.color,
    accentLine: true,
    title: `${b.cat}: ${b.title}`,
    titleColor: b.color,
    body: [
      { text: b.desc, fontSize: 13 }
    ]
  });
});

// ==========================================
// SLIDE 9: Cenário Nacional (Dados Reais)
// ==========================================
const slide9 = pptx.addSlide();
setBackground(slide9);
addHeader(slide9, 'O impacto dos acidentes de trabalho no Brasil', 'Dados Reais do Brasil');

// 3 stats cards
const statsNacionais = [
  { num: '724.228', title: 'Acidentes em 2024', desc: 'Registros oficiais de acidentes de trabalho no ano.' },
  { num: '8.8 Milhões', title: 'Acidentes Acumulados', desc: 'Registros acumulados entre 2012 e 2024.' },
  { num: '32.000+', title: 'Mortes Ocupacionais', desc: 'Mortes relacionadas ao trabalho de 2012 a 2024.' }
];

statsNacionais.forEach((st, idx) => {
  const x = 0.5 + idx * 4.2;
  
  slide9.addText(st.num, {
    x, y: 1.6, w: 3.93, h: 0.6,
    fontSize: 34, fontFace: 'Arial', bold: true, color: COLORS.RED, align: 'center'
  });

  slide9.addText(st.title, {
    x, y: 2.2, w: 3.93, h: 0.3,
    fontSize: 14, fontFace: 'Arial', bold: true, color: COLORS.NAVY, align: 'center'
  });

  slide9.addText(st.desc, {
    x, y: 2.5, w: 3.93, h: 0.6,
    fontSize: 12, fontFace: 'Arial', color: COLORS.TEXT_MUTED, align: 'center'
  });
});

// Risk factors and consequences in cards below
addCard(slide9, {
  x: 0.5, y: 3.3, w: 5.9, h: 1.6,
  accentLine: true,
  border: COLORS.RED,
  title: '+30% Risco de Acidentes',
  body: [
    { text: 'Como apontado por estudos divulgados por especialistas em Segurança do Trabalho, o uso inadequado de EPIs pode aumentar em até 30% o risco de acidentes ocupacionais.', fontSize: 11.5 }
  ]
});

addCard(slide9, {
  x: 6.9, y: 3.3, w: 5.9, h: 1.6,
  accentLine: true,
  border: COLORS.RED,
  title: 'Até +60% Risco de Acidentes Graves',
  body: [
    { text: 'Estudos citados por profissionais da área de Segurança do Trabalho indicam que a ausência ou utilização incorreta de EPIs pode elevar significativamente a ocorrência de acidentes graves.', fontSize: 11.5 }
  ]
});

// Impact summary callout box at the bottom
addCard(slide9, {
  x: 0.5, y: 5.1, w: 12.33, h: 1.4,
  bg: COLORS.LIGHT_BLUE,
  border: COLORS.BLUE,
  title: 'Impactos Diretos dos Acidentes',
  body: [
    { text: 'Os acidentes geram: afastamentos, processos trabalhistas, multas, perda de produtividade, custos previdenciários e graves danos à reputação e à imagem institucional da empresa.', fontSize: 12 }
  ]
});

// ==========================================
// SLIDE 10: Conclusão
// ==========================================
const slide10 = pptx.addSlide();
setBackground(slide10);
addHeader(slide10, 'Por que o Sistema de Monitoramento de EPIs?', 'Conclusão');

// Large executive quote block on the left
slide10.addShape(pptx.shapes.RECTANGLE, {
  x: 0.5, y: 1.8, w: 6.0, h: 4.8,
  fill: { color: COLORS.LIGHT_BLUE },
  line: { color: COLORS.BLUE, width: 1 }
});

slide10.addText('“Nosso projeto não é apenas um sistema de controle. Ele é uma ferramenta estratégica que auxilia a Facchini na proteção de seus colaboradores, na redução de custos operacionais e no fortalecimento dos processos de segurança e conformidade.”', {
  x: 0.9, y: 2.4, w: 5.2, h: 3.6,
  fontSize: 18,
  fontFace: 'Arial',
  italic: true,
  bold: true,
  color: COLORS.NAVY,
  lineSpacing: 26,
});

// Bullet list on the right
addCard(slide10, {
  x: 6.8, y: 1.8, w: 5.7, h: 4.8,
  accentLine: true,
  title: 'Diretrizes Estratégicas Recomendadas',
  body: [
    { text: 'Apresentação detalhada da plataforma ao SESMT e TI da Facchini.', bullet: true },
    { text: 'Definição do escopo piloto em uma das unidades da empresa.', bullet: true },
    { text: 'Estruturação do cronograma de integração de sistemas (ERP/RH).', bullet: true },
    { text: 'Alinhamento financeiro e de governança corporativa.', bullet: true },
  ]
});

// ==========================================
// SLIDE 11: Encerramento (Dark Theme)
// ==========================================
const slide11 = pptx.addSlide();
setBackground(slide11, true);

// Title
slide11.addText('MUITO OBRIGADO!', {
  x: 1.0,
  y: 2.2,
  w: 11.33,
  h: 0.8,
  fontSize: 40,
  fontFace: 'Arial',
  bold: true,
  color: COLORS.WHITE,
  align: 'center'
});

// Accent bar
slide11.addShape(pptx.shapes.RECTANGLE, {
  x: 5.16,
  y: 3.2,
  w: 3.0,
  h: 0.05,
  fill: { color: COLORS.ORANGE }
});

// Text
slide11.addText('Estamos à disposição para construir o futuro da segurança na Facchini.', {
  x: 1.0,
  y: 3.8,
  w: 11.33,
  h: 0.5,
  fontSize: 16,
  fontFace: 'Arial',
  color: COLORS.ORANGE,
  bold: true,
  align: 'center'
});

// Brand subtitle
slide11.addText('SISTEMA INTELIGENTE DE MONITORAMENTO DE EPIs', {
  x: 1.0,
  y: 4.8,
  w: 11.33,
  h: 0.8,
  fontSize: 14,
  fontFace: 'Arial',
  color: COLORS.WHITE,
  align: 'center',
  bold: true,
  letterSpacing: 2
});

// Save presentation
pptx.writeFile({ fileName: 'Apresentacao_EPI_Facchini.pptx' })
  .then(fileName => {
    console.log(`Presentation successfully created: ${fileName}`);
  })
  .catch(err => {
    console.error('Error creating presentation:', err);
    process.exit(1);
  });

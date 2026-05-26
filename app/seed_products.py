"""
Script CLI para popular o banco de dados com produtos de teste.

Uso:
    python -m app.seed_products

O script é idempotente: se já existirem produtos no banco, ele avisa e não cria duplicatas.
Produtos com nomes já existentes são ignorados (skip).
"""

import sys

from app.database.unit_of_work import UnitOfWork


SEED_PRODUCTS = [
    # ── Hardware ──
    {
        "name": "Processador AMD Ryzen 7 5700X",
        "description": "Processador de alta performance com 8 núcleos e 16 threads, clock de até 4.6GHz, ideal para jogos de última geração e renderização pesada.",
        "price": 1149.90,
        "category": "Hardware",
        "stock": 45,
    },
    {
        "name": "Memória RAM Corsair Vengeance LPX 16GB (2x8GB) DDR4",
        "description": "Kit de memória RAM de alto desempenho operando em 3200MHz, otimizada para as plataformas Intel e AMD mais recentes.",
        "price": 315.00,
        "category": "Hardware",
        "stock": 64,
    },
    {
        "name": "Fonte MSI Mag A650BN 650W",
        "description": "Fonte de alimentação de 650W com certificação 80 Plus Bronze e PFC ativo, garantindo eficiência e proteção para o PC.",
        "price": 349.00,
        "category": "Hardware",
        "stock": 27,
    },
    {
        "name": "Placa de Vídeo NVIDIA RTX 4060 Ti 8GB",
        "description": "GPU de última geração com arquitetura Ada Lovelace, 8GB GDDR6, ray tracing em tempo real e DLSS 3 para desempenho excepcional em 1080p e 1440p.",
        "price": 2899.90,
        "category": "Hardware",
        "stock": 15,
    },
    {
        "name": "Placa-Mãe Gigabyte B550M AORUS PRO-P",
        "description": "Placa-mãe micro-ATX com chipset B550, suporte a Ryzen 5000, DDR4 até 5200MHz, PCIe 4.0 e M.2 NVMe dual.",
        "price": 649.00,
        "category": "Hardware",
        "stock": 22,
    },
    {
        "name": "Cooler Master Hyper 212 Black Edition",
        "description": "Cooler para processador com 4 heatpipes diretos, dissipador em alumínio e ventoinha de 120mm com iluminação RGB.",
        "price": 189.90,
        "category": "Hardware",
        "stock": 50,
    },
    # ── Periféricos ──
    {
        "name": "Teclado Mecânico Gamer Logitech G413 SE",
        "description": "Teclado mecânico com switches táteis de alta velocidade, iluminação LED branca e acabamento em alumínio escovado.",
        "price": 389.00,
        "category": "Periféricos",
        "stock": 120,
    },
    {
        "name": "Mouse Sem Fio Razer DeathAdder V2 X Hyperspeed",
        "description": "Mouse ergonômico gamer sem fio com sensor avançado de 14.000 DPI e switches mecânicos de longa durabilidade.",
        "price": 279.90,
        "category": "Periféricos",
        "stock": 0,
    },
    {
        "name": "Headset Gamer HyperX Cloud III",
        "description": "Headset com áudio surround 7.1, microfone destacável com cancelamento de ruído e almofadas de espuma com memória para conforto prolongado.",
        "price": 449.90,
        "category": "Periféricos",
        "stock": 38,
    },
    {
        "name": "Webcam Logitech C920 HD Pro",
        "description": "Webcam Full HD 1080p com autofoco, microfones duplos integrados e correção de luz automática para streaming e videoconferências.",
        "price": 399.00,
        "category": "Periféricos",
        "stock": 55,
    },
    {
        "name": "Mousepad Gamer SteelSeries QcK Large",
        "description": "Mousepad em tecido com base de borracha antiderrapante, tamanho 450x400mm, superfície otimizada para sensores ópticos e a laser.",
        "price": 89.90,
        "category": "Periféricos",
        "stock": 200,
    },
    # ── Monitores ──
    {
        "name": "Monitor Gamer Asus Tuf 27\" Curvo",
        "description": "Monitor curvatura 1500R, resolução Full HD, taxa de atualização de 165Hz e tempo de resposta de 1ms com tecnologia FreeSync.",
        "price": 1450.00,
        "category": "Monitores",
        "stock": 18,
    },
    {
        "name": "Monitor LG UltraWide 34\" IPS",
        "description": "Monitor ultrawide 21:9 com resolução WFHD 2560x1080, cores sRGB 99% e tecnologia HDR10 para produtividade e entretenimento.",
        "price": 1899.00,
        "category": "Monitores",
        "stock": 12,
    },
    {
        "name": "Monitor Samsung Odyssey G4 24\" 240Hz",
        "description": "Monitor gaming com taxa de atualização de 240Hz, tempo de resposta de 1ms, tecnologia G-Sync Compatible e painel IPS para competitivo.",
        "price": 1699.00,
        "category": "Monitores",
        "stock": 8,
    },
    # ── Armazenamento ──
    {
        "name": "SSD Kingston NV2 1TB M.2 NVMe",
        "description": "Armazenamento ultra rápido com velocidades de leitura de até 3500MB/s e gravação de até 2100MB/s.",
        "price": 420.50,
        "category": "Armazenamento",
        "stock": 85,
    },
    {
        "name": "HD Seagate Barracuda 2TB",
        "description": "Disco rígido de 2TB com 7200RPM, interface SATA 6Gbps e cache de 256MB para armazenamento em massa confiável.",
        "price": 289.00,
        "category": "Armazenamento",
        "stock": 40,
    },
    {
        "name": "SSD Samsung 990 Pro 2TB M.2 NVMe",
        "description": "SSD de alto desempenho com velocidades de leitura de até 7450MB/s e gravação de até 6900MB/s, ideal para criadores de conteúdo e gamers.",
        "price": 1199.00,
        "category": "Armazenamento",
        "stock": 25,
    },
    # ── Redes ──
    {
        "name": "Roteador TP-Link Archer AX12 Wi-Fi 6",
        "description": "Roteador dual-band Gigabit com a tecnologia Wi-Fi 6 mais recente, garantindo maior velocidade e menor latência para múltiplos dispositivos.",
        "price": 299.90,
        "category": "Redes",
        "stock": 32,
    },
    {
        "name": "Placa de Rede TP-Link Archer TX50E AX3000",
        "description": "Placa de rede Wi-Fi 6 PCIe com Bluetooth 5.2, velocidade de até 2402Mbps em 5GHz e suporte a MU-MIMO para conexões estáveis.",
        "price": 249.00,
        "category": "Redes",
        "stock": 30,
    },
    {
        "name": "Switch TP-Link TL-SG1008D 8 Portas Gigabit",
        "description": "Switch não gerenciável de 8 portas Gigabit com tecnologia Green Ethernet para economia de energia e plug-and-play.",
        "price": 159.00,
        "category": "Redes",
        "stock": 45,
    },
    # ── Notebooks ──
    {
        "name": "Notebook Acer Nitro 5 Ryzen 5 RTX 3050",
        "description": "Notebook gamer com processador Ryzen 5 5600H, GPU RTX 3050 4GB, 8GB DDR4, SSD 512GB NVMe e tela 15.6\" FHD 144Hz.",
        "price": 4299.00,
        "category": "Notebooks",
        "stock": 10,
    },
    {
        "name": "Notebook Lenovo IdeaPad 3 Intel i5 12ª Geração",
        "description": "Notebook para produtividade com Intel i5-1235U, 8GB DDR4, SSD 256GB NVMe e tela 15.6\" FHD IPS antirreflexo.",
        "price": 3199.00,
        "category": "Notebooks",
        "stock": 14,
    },
    # ── Cadeiras e Mesas ──
    {
        "name": "Cadeira Gamer ThunderX3 EC3",
        "description": "Cadeira gamer com encosto reclinável até 180°, apoio lombar e de pescoço ajustáveis, estrutura em aço e estofado em tecido respirável.",
        "price": 899.00,
        "category": "Mobiliário",
        "stock": 20,
    },
    {
        "name": "Mesa Gamer Levity G-LP 1.80m",
        "description": "Mesa gamer com tampo de 180x60cm em MDF de alta resistência, suporte para monitor, porta-copos e gerenciamento de cabos integrado.",
        "price": 599.00,
        "category": "Mobiliário",
        "stock": 16,
    },
    # ── Áudio ──
    {
        "name": "Caixa de Som JBL Charge 5",
        "description": "Caixa de som portátil Bluetooth com som potente e graves profundos, bateria de 20 horas, resistência IP67 à água e poeira.",
        "price": 649.00,
        "category": "Áudio",
        "stock": 35,
    },
    {
        "name": "Fone de Ouvido Bluetooth Sony WH-1000XM5",
        "description": "Fone over-ear com cancelamento de ruído líder do mercado, áudio de alta resolução, bateria de 30 horas e conforto premium para uso prolongado.",
        "price": 2199.00,
        "category": "Áudio",
        "stock": 9,
    },
]


def seed_products():
    """Popula o banco de dados com produtos de teste."""
    created = 0
    skipped = 0

    with UnitOfWork() as uow:
        for product_data in SEED_PRODUCTS:
            existing = uow.products.get_product_by_name(product_data["name"])
            if existing:
                skipped += 1
                continue

            uow.products.create_product(
                name=product_data["name"],
                description=product_data["description"],
                price=product_data["price"],
                category=product_data["category"],
                stock=product_data["stock"],
            )
            created += 1

    print(f"✅ Seed de produtos concluído!")
    print(f"   Criados: {created}")
    print(f"   Ignorados (já existiam): {skipped}")
    print(f"   Total no catálogo: {created + skipped} produtos")


if __name__ == "__main__":
    seed_products()
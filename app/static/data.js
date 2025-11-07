// Sample species data with taxonomy hierarchy
const speciesData = [
    {
        id: 1,
        commonName: "Bald Eagle",
        scientificName: "Haliaeetus leucocephalus",
        kingdom: "Animalia",
        phylum: "Chordata",
        class: "Aves",
        order: "Accipitriformes",
        family: "Accipitridae",
        genus: "Haliaeetus",
        species: "H. leucocephalus",
        status: "common",
        description: "The bald eagle is a bird of prey found in North America. A sea eagle, it has two known subspecies and forms a species pair with the white-tailed eagle. Its range includes most of Canada and Alaska, all of the contiguous United States, and northern Mexico.",
        habitat: "Found near large bodies of open water with abundant food supply and old-growth trees for nesting.",
        diet: "Primarily fish, but also birds, reptiles, amphibians, invertebrates such as crabs, and mammals including rabbits and muskrats.",
        icon: "🦅"
    },
    {
        id: 2,
        commonName: "Gray Wolf",
        scientificName: "Canis lupus",
        kingdom: "Animalia",
        phylum: "Chordata",
        class: "Mammalia",
        order: "Carnivora",
        family: "Canidae",
        genus: "Canis",
        species: "C. lupus",
        status: "threatened",
        description: "The gray wolf, also known as the timber wolf, is a large canine native to Eurasia and North America. It is the largest extant member of its family, with males averaging 40 kg and females 37 kg.",
        habitat: "Wolves can thrive in a diversity of habitats from the tundra to woodlands, forests, grasslands and deserts.",
        diet: "Carnivorous, primarily feeding on ungulates such as deer, elk, moose, and bison. Also hunts smaller prey and occasionally feeds on carrion.",
        icon: "🐺"
    },
    {
        id: 3,
        commonName: "Monarch Butterfly",
        scientificName: "Danaus plexippus",
        kingdom: "Animalia",
        phylum: "Arthropoda",
        class: "Insecta",
        order: "Lepidoptera",
        family: "Nymphalidae",
        genus: "Danaus",
        species: "D. plexippus",
        status: "threatened",
        description: "The monarch butterfly is a milkweed butterfly in the family Nymphalidae. Other common names include milkweed, common tiger, wanderer, and black-veined brown. It is among the most familiar of North American butterflies.",
        habitat: "Found in open areas including fields, meadows, weedy areas, marshes, and roadsides. Requires milkweed plants for reproduction.",
        diet: "Adults feed on nectar from a variety of flowers. Larvae feed exclusively on milkweed plants.",
        icon: "🦋"
    },
    {
        id: 4,
        commonName: "Red Fox",
        scientificName: "Vulpes vulpes",
        kingdom: "Animalia",
        phylum: "Chordata",
        class: "Mammalia",
        order: "Carnivora",
        family: "Canidae",
        genus: "Vulpes",
        species: "V. vulpes",
        status: "common",
        description: "The red fox is the largest of the true foxes and one of the most widely distributed members of the order Carnivora. It is present across the entire Northern Hemisphere including most of North America, Europe and Asia.",
        habitat: "Highly adaptable, found in forests, grasslands, mountains, and deserts. Also common in urban and suburban areas.",
        diet: "Omnivorous with a varied diet including small mammals, birds, eggs, insects, fruits, and vegetables.",
        icon: "🦊"
    },
    {
        id: 5,
        commonName: "American Black Bear",
        scientificName: "Ursus americanus",
        kingdom: "Animalia",
        phylum: "Chordata",
        class: "Mammalia",
        order: "Carnivora",
        family: "Ursidae",
        genus: "Ursus",
        species: "U. americanus",
        status: "common",
        description: "The American black bear is a medium-sized bear native to North America. It is the continent's smallest and most widely distributed bear species. Despite their name, black bears show a wide variation in color.",
        habitat: "Typically found in forested areas, but will leave forests in search of food. Can adapt to various habitats including swamps, mountains, and even urban areas.",
        diet: "Omnivorous, with diet consisting of vegetation, fruits, nuts, insects, honey, and occasionally fish and small mammals.",
        icon: "🐻"
    },
    {
        id: 6,
        commonName: "Great Horned Owl",
        scientificName: "Bubo virginianus",
        kingdom: "Animalia",
        phylum: "Chordata",
        class: "Aves",
        order: "Strigiformes",
        family: "Strigidae",
        genus: "Bubo",
        species: "B. virginianus",
        status: "common",
        description: "The great horned owl is a large owl native to the Americas. It is an extremely adaptable bird with a vast range and is the most widely distributed true owl in the Americas.",
        habitat: "Found in diverse habitats including forests, swamps, deserts, and urban areas. Prefers areas with open hunting grounds and large trees for nesting.",
        diet: "Carnivorous, feeding on mammals such as rabbits, skunks, and rodents, as well as birds, reptiles, and amphibians.",
        icon: "🦉"
    },
    {
        id: 7,
        commonName: "White-tailed Deer",
        scientificName: "Odocoileus virginianus",
        kingdom: "Animalia",
        phylum: "Chordata",
        class: "Mammalia",
        order: "Artiodactyla",
        family: "Cervidae",
        genus: "Odocoileus",
        species: "O. virginianus",
        status: "common",
        description: "The white-tailed deer, also known as the whitetail or Virginia deer, is a medium-sized deer native to North America, Central America, and South America. It is named for its distinctive white tail.",
        habitat: "Prefers mixed farmland and forests, but highly adaptable and found in various habitats from forests to grasslands and even suburban areas.",
        diet: "Herbivorous, feeding on leaves, twigs, fruits, nuts, grass, and sometimes agricultural crops.",
        icon: "🦌"
    },
    {
        id: 8,
        commonName: "California Condor",
        scientificName: "Gymnogyps californianus",
        kingdom: "Animalia",
        phylum: "Chordata",
        class: "Aves",
        order: "Accipitriformes",
        family: "Cathartidae",
        genus: "Gymnogyps",
        species: "G. californianus",
        status: "endangered",
        description: "The California condor is a New World vulture and the largest North American land bird. It became extinct in the wild in 1987, but has since been reintroduced to northern Arizona and southern Utah, coastal mountains of California, and northern Baja California.",
        habitat: "Rocky shrubland, coniferous forest, and oak savanna. Requires large areas of habitat for foraging.",
        diet: "Scavenger, feeding exclusively on carrion including deer, cattle, sheep, rabbits, and rodents.",
        icon: "🦅"
    },
    {
        id: 9,
        commonName: "Honeybee",
        scientificName: "Apis mellifera",
        kingdom: "Animalia",
        phylum: "Arthropoda",
        class: "Insecta",
        order: "Hymenoptera",
        family: "Apidae",
        genus: "Apis",
        species: "A. mellifera",
        status: "common",
        description: "The western honey bee or European honey bee is the most common of the 7-12 species of honey bees worldwide. It is believed to have originated in Africa or Asia and spread naturally through Europe.",
        habitat: "Highly adaptable, living in managed hives or natural cavities. Found in diverse environments from forests to urban areas.",
        diet: "Feeds on nectar and pollen from flowers. Nectar is converted to honey for storage.",
        icon: "🐝"
    },
    {
        id: 10,
        commonName: "American Alligator",
        scientificName: "Alligator mississippiensis",
        kingdom: "Animalia",
        phylum: "Chordata",
        class: "Reptilia",
        order: "Crocodilia",
        family: "Alligatoridae",
        genus: "Alligator",
        species: "A. mississippiensis",
        status: "common",
        description: "The American alligator, sometimes referred to colloquially as a gator or common alligator, is a large crocodilian reptile native to the Southeastern United States.",
        habitat: "Freshwater environments such as ponds, marshes, wetlands, rivers, lakes, and swamps.",
        diet: "Carnivorous, feeding on fish, birds, turtles, snakes, small mammals, and occasionally larger prey.",
        icon: "🐊"
    },
    {
        id: 11,
        commonName: "Ruby-throated Hummingbird",
        scientificName: "Archilochus colubris",
        kingdom: "Animalia",
        phylum: "Chordata",
        class: "Aves",
        order: "Apodiformes",
        family: "Trochilidae",
        genus: "Archilochus",
        species: "A. colubris",
        status: "common",
        description: "The ruby-throated hummingbird is a species of hummingbird that generally spends the winter in Central America, Mexico, and Florida, and migrates to Canada and other parts of Eastern North America for the summer to breed.",
        habitat: "Open woodlands, gardens, and areas with flowering plants. Common in suburban gardens with feeders.",
        diet: "Feeds on nectar from flowers and sugar water from feeders. Also consumes small insects and spiders for protein.",
        icon: "🐦"
    },
    {
        id: 12,
        commonName: "Luna Moth",
        scientificName: "Actias luna",
        kingdom: "Animalia",
        phylum: "Arthropoda",
        class: "Insecta",
        order: "Lepidoptera",
        family: "Saturniidae",
        genus: "Actias",
        species: "A. luna",
        status: "rare",
        description: "The Luna moth is a Nearctic moth in the family Saturniidae, subfamily Saturniinae, a group commonly known as giant silk moths. It has lime-green colored wings and a white body.",
        habitat: "Deciduous hardwood forests. Larvae feed on leaves of walnut, hickory, sweetgum, and persimmon trees.",
        diet: "Adults do not eat. Larvae feed on tree leaves including walnut, hickory, sweetgum, and persimmon.",
        icon: "🦋"
    }
];

// Build taxonomy hierarchy from species data
function buildTaxonomyHierarchy() {
    const hierarchy = {
        kingdom: {},
        phylum: {},
        class: {},
        order: {},
        family: {}
    };

    speciesData.forEach(species => {
        // Kingdom
        if (!hierarchy.kingdom[species.kingdom]) {
            hierarchy.kingdom[species.kingdom] = { name: species.kingdom, children: {} };
        }

        // Phylum
        const kingdomNode = hierarchy.kingdom[species.kingdom];
        if (!kingdomNode.children[species.phylum]) {
            kingdomNode.children[species.phylum] = { name: species.phylum, children: {} };
        }

        // Class
        const phylumNode = kingdomNode.children[species.phylum];
        if (!phylumNode.children[species.class]) {
            phylumNode.children[species.class] = { name: species.class, children: {} };
        }

        // Order
        const classNode = phylumNode.children[species.class];
        if (!classNode.children[species.order]) {
            classNode.children[species.order] = { name: species.order, children: {} };
        }

        // Family
        const orderNode = classNode.children[species.order];
        if (!orderNode.children[species.family]) {
            orderNode.children[species.family] = { name: species.family, species: [] };
        }

        // Add species to family
        orderNode.children[species.family].species.push(species);
    });

    return hierarchy;
}
